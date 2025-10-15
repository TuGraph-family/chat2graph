from abc import abstractmethod
import ast
import json
from typing import Callable, Dict, List, Tuple

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.prompt.workflow_generator import (
    get_actions_prompt_template,
    optimize_expert_prompt_template,
    optimize_op_prompt_template,
)
from app.core.reasoner.model_service_factory import ModelService, ModelServiceFactory
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import (
    AgenticConfigSection,
    OptimizeAction,
    OptimizeObject,
    OptimizeResp,
    WorkflowLogFormat,
)
from app.core.workflow.workflow_generator.mcts_workflow_generator.utils import (
    JsonValue,
    format_yaml_with_anchor,
    generate_json,
)


class Expander:
    @abstractmethod
    async def expand(
        self, task_tesc: str, current_config: Dict[str, str], round_context: WorkflowLogFormat
    ) -> Tuple[List[OptimizeAction], OptimizeResp]: ...


class LLMExpander(Expander):
    def __init__(self):
        super().__init__()
        self._llm: ModelService = ModelServiceFactory.create(
            model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE
        )
        self.max_retry = 5
        self.all_context_section = [
            "task description",
            "actions",
            "operators",
            "experts",
            "score",
            "modification",
            "reflection",
            "feedbacks",
        ]
        self.section_desc = {
            "task description": "A detailed explanation of the current task within the agent system.",  # noqa: E501
            "actions": "The available actions operator can perform.",
            "operators": "The definition of current systems's operators.",
            "experts": "The definition of current systems's experts.",
            "score": "The average score or performance metric of the current system.",
            "modification": "A description of change or modification that were made to arrive at the current system.",  # noqa: E501
            "reflection": "Reflections on mistakes and suggestions for improvement",
            "feedbacks": "The optimization actions taken from the current system and the resulting feedback",  # noqa: E501
        }
        self.job_id = "[LLMExpander]expand"  # TODO: uuid

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

    async def _get_optimize_actions(
        self,
        task_desc: str,
        current_actions: str,
        current_operators: str,
        current_experts: str,
        round_context: WorkflowLogFormat,
    ) -> List[OptimizeAction]:
        context = self.format_context(
            sections=self.all_context_section,
            sections_context={
                "task description": task_desc,
                "actions": format_yaml_with_anchor(
                    current_actions, key=AgenticConfigSection.ACTIONS.value, fields=["desc"]
                ),
                "operators": current_operators,
                "experts": current_experts,
                "score": f"{round_context.score}",
                "modification": json.dumps(
                    round_context.modifications, indent=2, ensure_ascii=False
                ),
                "reflection": json.dumps(round_context.reflection, indent=2, ensure_ascii=False),
                "feedbacks": json.dumps(round_context.feedbacks, indent=2, ensure_ascii=False),
            },
        )

        prompt = get_actions_prompt_template.format(context=context)

        def filter(results: List[JsonValue]) -> JsonValue:
            for actions in results:
                if isinstance(actions, list):
                    for action in actions:
                        OptimizeAction.model_validate(action)

                    return actions
                else:
                    raise Exception("the result should be a json list")

            return None

        resp = await self._generate(prompt=prompt, job_id=self.job_id, filter=filter, extra_messages=[])
        try:
            result: List[OptimizeAction] = []
            if isinstance(resp, list):
                for action in resp:
                    result.append(OptimizeAction.model_validate(action))
                return result
        except Exception as e:
            print(f"[LLMExpander][_get_optimize_actions] failed, reason={e}")
            return []

        return []

    async def _expand_operator(
        self,
        task_desc: str,
        actions: str,
        current_operators: str,
        round_context: WorkflowLogFormat,
        optimize_acitons: List[OptimizeAction],
        extra_messages: List[ModelMessage],
    ) -> OptimizeResp:
        if extra_messages is None:
            extra_messages = []
        not_need_section = ["experts"]
        context = self.format_context(
            sections=[
                section for section in self.all_context_section if section not in not_need_section
            ],
            sections_context={
                "task description": task_desc,
                "actions": format_yaml_with_anchor(
                    actions, key=AgenticConfigSection.ACTIONS.value, fields=["desc"]
                ),
                "operators": current_operators,
                "score": f"{round_context.score}",
                "modification": json.dumps(
                    round_context.modifications, indent=2, ensure_ascii=False
                ),
                "reflection": json.dumps(round_context.reflection, indent=2, ensure_ascii=False),
                "feedbacks": json.dumps(round_context.feedbacks, indent=2, ensure_ascii=False),
            },
        )

        prompt = optimize_op_prompt_template.format(
            context=context,
            optimize_actions=optimize_acitons,
        )

        def filter(results: List[JsonValue]) -> JsonValue:
            for optimize_resp in results:
                # syntax check
                resp = OptimizeResp.model_validate(optimize_resp)

                # reference check
                if AgenticConfigSection.OPERATORS.value not in resp.new_configs:
                    raise Exception("missing `operators` field in new_configs field.")

                op_fields = ["instruction", "output_schema", "actions"]
                actions_format = format_yaml_with_anchor(
                    actions, key=AgenticConfigSection.ACTIONS.value, fields=[]
                )
                action_list = ast.literal_eval(actions_format)
                ops_format = format_yaml_with_anchor(
                    resp.new_configs[AgenticConfigSection.OPERATORS.value],
                    AgenticConfigSection.OPERATORS.value,
                    fields=op_fields,
                )
                op_list = ast.literal_eval(ops_format)
                for action in action_list:
                    if not isinstance(action, Dict) or "name" not in action:
                        raise Exception(f"invalid action: {action}")

                action_name_list = [action.get("name", "") for action in action_list]
                error_messages: List[str] = []
                for op in op_list:
                    if not isinstance(op, Dict):
                        error_messages.append(f"invalid operator: {op}, it should be a json dict.")
                        continue

                    for field in op_fields:
                        if field not in op:
                            error_messages.append(
                                f"invalid operator: {op}, it must contain `{field}` field."
                            )

                    op_actions = op.get("actions", None)
                    if not isinstance(op_actions, List):
                        error_messages.append(
                            f"invalid actions syntax {op_actions}, it should be a json list."
                        )
                        continue

                    for action in op_actions:
                        if action not in action_name_list:
                            error_messages.append(
                                f"unknown action reference {action}, the referenced action must be in the {action_name_list} list"  # noqa: E501
                            )

                if len(error_messages) > 0:
                    raise Exception(f"{error_messages}")
                return optimize_resp

            return None

        optimize_resp = await self._generate(
            prompt=prompt, job_id=self.job_id, filter=filter, extra_messages=extra_messages
        )
        try:
            return OptimizeResp.model_validate(optimize_resp)
        except Exception as e:
            print(f"[LLMExpander][_expand_operator] failed, reason={e}")
            return OptimizeResp(modifications=[], new_configs={})

    async def _expand_experts(
        self,
        task_desc: str,
        operators: str,
        current_experts: str,
        round_context: WorkflowLogFormat,
        optimize_acitons: List[OptimizeAction],
        extra_messages: List[ModelMessage],
    ) -> OptimizeResp:
        if extra_messages is None:
            extra_messages = []
        not_need_section = ["actions"]
        context = self.format_context(
            sections=[
                section for section in self.all_context_section if section not in not_need_section
            ],
            sections_context={
                "task description": task_desc,
                "operators": format_yaml_with_anchor(
                    operators,
                    key=AgenticConfigSection.OPERATORS.value,
                    fields=["instruction", "output_schema"],
                ),
                "experts": current_experts,
                "score": f"{round_context.score}",
                "modification": json.dumps(
                    round_context.modifications, indent=2, ensure_ascii=False
                ),
                "reflection": json.dumps(round_context.reflection, indent=2, ensure_ascii=False),
                "feedbacks": json.dumps(round_context.feedbacks, indent=2, ensure_ascii=False),
            },
        )

        prompt = optimize_expert_prompt_template.format(
            context=context,
            optimize_actions=optimize_acitons,
        )

        def filter(results: List[JsonValue]) -> JsonValue:
            for optimize_resp in results:
                # syntax check
                resp = OptimizeResp.model_validate(optimize_resp)

                # reference check
                if AgenticConfigSection.EXPERTS.value not in resp.new_configs:
                    raise Exception("missing `experts` field in new_configs.")

                ops_format = format_yaml_with_anchor(
                    operators, key=AgenticConfigSection.OPERATORS.value, fields=[]
                )
                op_list = ast.literal_eval(ops_format)
                for op in op_list:
                    if not isinstance(op, Dict) or "name" not in op:
                        raise Exception(f"invalid operator: {op}")
                op_name_list = [op.get("name", "") for op in op_list]

                experts_fields = ["profile", "reasoner", "workflow"]
                experts_format = format_yaml_with_anchor(
                    resp.new_configs[AgenticConfigSection.EXPERTS.value],
                    key=AgenticConfigSection.EXPERTS.value,
                    fields=experts_fields,
                    need_anchor_name=False,
                )
                expert_list = ast.literal_eval(experts_format)

                error_messages: List[str] = []
                for expert in expert_list:
                    if not isinstance(expert, Dict):
                        error_messages.append(
                            f"invalid expert: {expert}, it should be a json dict."
                        )
                        continue

                    for field in experts_fields:
                        if field not in expert:
                            error_messages.append(
                                f"invalid expert: {expert}, it must contain `{field}` field."
                            )

                    expert_workflow = expert.get("workflow", None)
                    if not isinstance(expert_workflow, List):
                        error_messages.append(
                            f"invalid workflow syntax: {expert_workflow}, it must be a two-dimensional array "  # noqa: E501
                        )
                        continue

                    for dependency_list in expert_workflow:
                        if not isinstance(dependency_list, List):
                            error_messages.append(
                                f"invalid workflow syntax: {dependency_list}, it must be a array"
                            )
                            continue
                        for op in dependency_list:
                            if op not in op_name_list:
                                error_messages.append(
                                    f"unknown operator reference {op}, the referenced action must be in the {op_list} list"  # noqa: E501
                                )

                if len(error_messages) > 0:
                    raise Exception(f"{error_messages}")

                return optimize_resp

            return None

        optimize_resp = await self._generate(
            prompt=prompt, job_id=self.job_id, filter=filter, extra_messages=extra_messages
        )
        try:
            return OptimizeResp.model_validate(optimize_resp)
        except Exception as e:
            print(f"[LLMExpander][_expand_experts] failed, reason={e}")
            return OptimizeResp(modifications=[], new_configs={})

    async def _generate(
        self,
        prompt: str,
        job_id: str,
        filter: Callable[[List[JsonValue]], JsonValue],
        extra_messages: List[ModelMessage],
    ) -> JsonValue:
        if extra_messages is None:
            extra_messages = []
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

    async def expand(
        self, task_tesc: str, current_config: Dict[str, str], round_context: WorkflowLogFormat
    ) -> Tuple[List[OptimizeAction], OptimizeResp]:
        current_actions = current_config.get(str(AgenticConfigSection.ACTIONS.value))
        current_ops = current_config.get(str(AgenticConfigSection.OPERATORS.value))
        current_experts = current_config.get(str(AgenticConfigSection.EXPERTS.value))
        if current_actions is None or current_ops is None or current_experts is None:
            raise Exception(
                f"[LLMExpander][expand] Cann't not find actions\
                    or operators or experts in current_config={current_config}" # noqa: 501
            )

        retry_count = 0
        while retry_count < self.max_retry:
            retry_count += 1
            try:
                optimize_actions = await self._get_optimize_actions(
                    task_desc=task_tesc,
                    current_actions=current_actions,
                    current_operators=current_ops,
                    current_experts=current_experts,
                    round_context=round_context,
                )
                if len(optimize_actions) != 0:
                    break
            except Exception:
                continue

        if len(optimize_actions) == 0:
            raise Exception("[expand] failed while get optimize actions")

        operator_optimize_actions = [
            action
            for action in optimize_actions
            if action.optimize_object == OptimizeObject.OPERATOR
        ]
        expert_optimize_actions = [
            action for action in optimize_actions if action.optimize_object == OptimizeObject.EXPERT
        ]

        all_result: OptimizeResp = OptimizeResp(modifications=[], new_configs={})
        if len(operator_optimize_actions) > 0:
            retry_count = 0
            extra_messages: List[ModelMessage] = []
            while retry_count < self.max_retry:
                retry_count += 1
                operator_optimize_result = await self._expand_operator(
                    task_desc=task_tesc,
                    actions=current_actions,
                    current_operators=current_ops,
                    round_context=round_context,
                    optimize_acitons=operator_optimize_actions,
                    extra_messages=extra_messages,
                )
                new_ops = operator_optimize_result.new_configs.get(
                    AgenticConfigSection.OPERATORS.value
                )
                if new_ops:
                    all_result.modifications.extend(operator_optimize_result.modifications)
                    all_result.new_configs.update(operator_optimize_result.new_configs)
                    break

                # TODO: add extra message to induce llm
        else:
            new_ops = current_ops

        if new_ops is  None:
            raise Exception("[LLMExpander][expand] new_ops is None")

        if len(expert_optimize_actions) > 0:
            retry_count = 0
            extra_messages = []
            while retry_count < self.max_retry:
                retry_count += 1
                expert_optimize_result = await self._expand_experts(
                    task_desc=task_tesc,
                    operators=new_ops,
                    current_experts=current_experts,
                    round_context=round_context,
                    optimize_acitons=expert_optimize_actions,
                    extra_messages=extra_messages,
                )
                if expert_optimize_result.new_configs.get(AgenticConfigSection.EXPERTS.value):
                    all_result.modifications.extend(expert_optimize_result.modifications)
                    all_result.new_configs.update(expert_optimize_result.new_configs)
                    break

                # TODO: add extra message to induce llm
        return optimize_actions, all_result
