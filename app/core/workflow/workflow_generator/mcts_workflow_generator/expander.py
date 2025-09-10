from abc import abstractmethod
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import OptimizeResp, WorkflowLogFormat, OptimizeAction, OptimizeObject, AgenticConfigSection
from app.core.workflow.workflow_generator.mcts_workflow_generator.utils import format_yaml_with_anchor, generate_json, JsonValue
from app.core.prompt.workflow_generator import optimize_op_prompt_template, get_actions_prompt_template, optimize_expert_prompt_template
from app.core.reasoner.model_service_factory import ModelServiceFactory, ModelService
from app.core.model.message import ModelMessage
from app.core.common.type import MessageSourceType
from app.core.common.system_env import SystemEnv
from typing import List, Dict, Any, Callable
import ast

class Expander:
    @abstractmethod
    async def expand(self, task_tesc: str, current_config: Dict[str, str], round_context: WorkflowLogFormat) -> OptimizeResp:
        ...


class LLMExpander(Expander):
    def __init__(self):
        super().__init__()
        self._llm: ModelService = ModelServiceFactory.create(model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
        self.max_retry = 5
        self.all_context_section = [
            "task description",
            "actions",
            "operators",
            "experts",
            "score",
            "modification",
            "experience",
            "feedbacks"
        ]
        self.section_desc = {
            "task description": "A detailed explanation of the current task within the agent system.",
            "actions": "The available actions operator can perform.",
            "operators": "The definition of current systems's operators.",
            "experts": "The definition of current systems's experts.",
            "score": "The average score or performance metric of the current system.",
            "modification": "A description of change or modification that were made to arrive at the current system.",
            "experience": "Insights and experiences gained from the modification.",
            "feedbacks": "Additional insights and experiences gained from further optimizing the current system.",
        }
        self.job_id = "[LLMExpander]expand"

    def format_context(self, sections: List[str], sections_context: Dict[str, str]) -> str:
        context_str = "The context describes the following aspects of the current system:\n"
        for idx, section in enumerate(sections, 1):
            if section not in self.all_context_section:
                raise ValueError(f"Unknown section {section}")
            context_str += f"({idx}) {section}: {self.section_desc[section]}\n"
        
        context_str += "\n"
        for section in sections:
            if section not in self.all_context_section:
                raise ValueError(f"Unknown section {section}")
            section_context = sections_context.get(section, "")
            context_str += f"**{section}**\n{section_context}\n\n" 
        
        return context_str

    async def _get_optimize_actions(self, task_desc: str, current_actions: str, current_operators: str, current_experts: str, round_context: WorkflowLogFormat) -> List[OptimizeAction]:
        context = self.format_context(
            sections=self.all_context_section,
            sections_context={
                "task description": task_desc,
                "actions": format_yaml_with_anchor(current_actions, key="actions", fields=["desc"]),
                "operators": current_operators,
                "experts": current_experts,
                "score": round_context.score,
                "modification": round_context.modifications,
                "experience": round_context.experience,
                "feedbacks": round_context.feedbacks,
            }
        )
        
        prompt = get_actions_prompt_template.format(
            context=context
        )


        
        def filter(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            fields = OptimizeAction.model_fields.keys()
            for result in results:
                for record in result:
                    for field in fields:
                        if field not in record:
                            raise Exception(f"{field} not in {result}") 
                return result
    
        resp = await self._generate(prompt=prompt, job_id=self.job_id, filter=filter)

        result: List[OptimizeAction] = []
        for action in resp:
            result.append(
                OptimizeAction.model_validate(action)
            )
        return result

    def _check(self, actions: str, optimize_resp: OptimizeResp) -> List[str]:
        error_messages: List[str] = []
        if "experts" not in optimize_resp.new_configs:
            error_messages.append(f"Cann't find experts in OptimizeResp={optimize_resp}")
            return error_messages
        
        if "operators" not in optimize_resp.new_configs:
            error_messages.append(f"Cann't find operators in OptimizeResp={optimize_resp}")
            return error_messages
        
        op_fields = ["instruction", "output_schema", "actions"]
        experts_fields = ["profile", "reasoner", "workflow"]
        actions_format = format_yaml_with_anchor(actions, "actions")
        ops_format = format_yaml_with_anchor(optimize_resp.new_configs["operators"], "operators", fields=op_fields)
        experts_format = format_yaml_with_anchor(optimize_resp.new_configs["experts"], "experts", fields=experts_fields, need_anchor_name=False)
        
        try:
            action_list = ast.literal_eval(actions_format)
            op_list = ast.literal_eval(ops_format)
            expert_list = ast.literal_eval(experts_format)
            
            for action in action_list:
                if not isinstance(action, Dict) or not "name" in action:
                    error_messages.append(f"invalid action: {action}")
            
            action_list = [action.get("name", "") for action in action_list]
            
            # check op_list
            for op in op_list:
                if not isinstance(op, Dict):
                    error_messages.append(f"invalid operator: {op}")
                    continue
                
                for field in op_fields:
                    if field not in op:
                        error_messages.append(f"invalid operator: {op}, missing {field}")
                
                op_actions = op.get("actions", None)
                if not isinstance(op_actions, List):
                    error_messages.append(f"invalid actions syntax {op_actions} in operator: {op}")
                    continue
                
                for action in op_actions:
                    if action not in action_list:
                        error_messages.append(f"unknown action reference {op_actions} in operator {op}, the referenced action must be in {action_list}")
            
            op_list = [op.get("name", "") for op in op_list]
            
            # check expert list
            for expert in expert_list:
                if not isinstance(expert, Dict):
                    error_messages.append(f"invalid expert: {expert}")
                    continue
                    
                for field in experts_fields:
                    if field not in expert:
                        error_messages.append(f"invalid expert: {expert}, missing {field}")
                
                expert_workflow = expert.get("workflow", None)
                if not isinstance(expert_workflow, List):
                    error_messages.append(f"invalid workflow: {expert_workflow} in {expert}")
                    continue
                    
                for dependenct_list in expert_workflow:
                    if not isinstance(dependenct_list, List):
                        error_messages.append(f"invalid workflow: {expert_workflow} in {expert}")
                        break
                    for op in dependenct_list:
                        if op not in op_list:
                            error_messages.append(f"unknown operator reference {op} in expert {expert}, the referenced action must be in operators list")

            return error_messages
        except Exception as e:
            print(f"[LLMExpander][_check] failed, reason={e}")
            return []    
        
    async def _expand_operator(self, task_desc: str, actions: str, current_operators: str, round_context: WorkflowLogFormat, optimize_acitons: List[OptimizeAction], extra_messages: List[ModelMessage] = []) ->OptimizeResp:
        not_need_section = ["experts"]
        context = self.format_context(
            sections=[section for section in self.all_context_section if section not in not_need_section],
            sections_context={
                "task description": task_desc,
                "actions": format_yaml_with_anchor(actions, key="actions", fields=["desc"]),
                "operators": current_operators,
                "score": round_context.score,
                "modification": round_context.modifications,
                "experience": round_context.experience,
                "feedbacks": round_context.feedbacks,
            }
        )
            
        prompt = optimize_op_prompt_template.format(
            context=context,
            optimize_actions=optimize_acitons,
            
        )
        

        def filter(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            fields = OptimizeResp.model_fields.keys()
            for result in results:
                for field in fields:
                    if field not in result:
                        raise Exception(f"{field} not in {result}") 
                return result
    
        optimize_resp = await self._generate(prompt=prompt, job_id=self.job_id, filter=filter, extra_messages=extra_messages)
        
        return OptimizeResp.model_validate(optimize_resp)
    
    async def _expand_experts(self, task_desc: str, operators: str, current_experts: str,  round_context: WorkflowLogFormat, optimize_acitons: List[OptimizeAction], extra_messages: List[ModelMessage] = []) -> OptimizeResp:
        not_need_section = ["actions"]
        context = self.format_context(
            sections=[section for section in self.all_context_section if section not in not_need_section],
            sections_context={
                "task description": task_desc,
                "operators": format_yaml_with_anchor(operators, key="operators", fields=["instruction", "output_schema"]),
                "experts": current_experts,
                "score": round_context.score,
                "modification": round_context.modifications,
                "experience": round_context.experience,
                "feedbacks": round_context.feedbacks,
            }
        )
            
        prompt = optimize_expert_prompt_template.format(
            context=context,
            optimize_actions=optimize_acitons,
        )
        
        def filter(results: JsonValue) -> JsonValue:
            fields = OptimizeResp.model_fields.keys()
            for result in results:
                for field in fields:
                    if field not in result:
                        raise Exception(f"{field} not in {result}") 
                return result
    
        optimize_resp = await self._generate(prompt=prompt, job_id=self.job_id, filter=filter, extra_messages=extra_messages)
        
        return OptimizeResp.model_validate(optimize_resp)
    
    async def _generate(self, prompt: str, job_id: str, filter: Callable[[JsonValue], JsonValue], extra_messages: List[ModelMessage] = [])->JsonValue:
        messages: List[ModelMessage] = []
        message = ModelMessage(
            payload=prompt,
            source_type=MessageSourceType.MODEL,
            job_id=job_id,
            step=1,
        )
        
        messages.append(message)
        messages.extend(extra_messages)
        result = await generate_json(
            model=self._llm,
            sys_prompt="", 
            max_retry=self.max_retry,
            messages=messages, 
            filter=filter,
        )
        
        return result
    
    async def expand(self, task_tesc: str, current_config: Dict[str, str], round_context: WorkflowLogFormat) -> OptimizeResp:
        current_actions = current_config.get(str(AgenticConfigSection.ACTIONS.value))
        current_ops = current_config.get(str(AgenticConfigSection.OPERATORS.value))
        current_experts = current_config.get(str(AgenticConfigSection.EXPERTS.value))
        if current_actions == None or current_ops == None or current_experts == None:
            raise Exception(f"[LLMExpander][expand] Cann't not find actions or operators or experts in current_config={current_config}")
        

        optimize_actions = await self._get_optimize_actions(
            task_desc=task_tesc, 
            current_actions=current_actions, 
            current_operators=current_ops, 
            current_experts=current_experts, 
            round_context=round_context
        )
        
        operator_optimize_actions = [action for action in optimize_actions if action.optimize_object == OptimizeObject.OPERATOR]
        expert_optimize_actions = [action for action in optimize_actions if action.optimize_object == OptimizeObject.EXPERT]
        all_result: OptimizeResp = OptimizeResp(
            modifications=[],
            new_configs={}
        )
            
        expand_times = 0
        extra_messages: List[ModelMessage] = []
        while expand_times < self.max_retry:
            expand_times += 1
            if len(operator_optimize_actions) > 0:
                operator_optimize_result = await self._expand_operator(
                    task_desc=task_tesc, 
                    actions=current_actions, 
                    current_operators=current_ops, 
                    round_context=round_context, 
                    optimize_acitons=operator_optimize_actions,
                    extra_messages=extra_messages
                )
                new_ops = operator_optimize_result.new_configs.get(str(AgenticConfigSection.OPERATORS.value))
                all_result.modifications.extend(operator_optimize_result.modifications)
                all_result.new_configs.update(operator_optimize_result.new_configs)
            else:
                new_ops = current_ops
            
            if new_ops == None:
                raise Exception(f"[LLMExpander][expand] new_ops is None")
            
            if len(expert_optimize_actions) > 0:
                expert_optimize_result = await self._expand_experts(
                    task_desc=task_tesc, 
                    operators=new_ops, 
                    current_experts=current_experts, 
                    round_context=round_context, 
                    optimize_acitons=expert_optimize_actions,
                    extra_messages=extra_messages
                )
                all_result.modifications.extend(expert_optimize_result.modifications)
                all_result.new_configs.update(expert_optimize_result.new_configs)

            error_messages = self._check(actions=current_actions, optimize_resp=all_result)
            if len(error_messages) == 0:
                break
            
            extra_messages.append(
                ModelMessage(
                    payload=f"{all_result}",
                    source_type=MessageSourceType.ACTOR,
                    job_id=self.job_id,
                    step=expand_times,
                )
            )
            
            extra_messages.append(
                ModelMessage(
                    payload=f"{error_messages}",
                    source_type=MessageSourceType.MODEL,
                    job_id=self.job_id,
                    step=expand_times+1,
                )
            )
            
        return all_result