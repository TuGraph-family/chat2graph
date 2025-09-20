from abc import abstractmethod
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import OptimizeResp, WorkflowLogFormat
from app.core.prompt.workflow_generator import optimize_prompt_template
from app.core.workflow.workflow_generator.llm_client import LLMClient
from app.core.common.system_env import SystemEnv

import re
import json

class Expander:
    @abstractmethod
    def expand(self, task_description: str, current_workflow: dict[str, str], round_context: WorkflowLogFormat) -> OptimizeResp:
        ...


class LLMExpander(Expander):
    def __init__(self):
        super().__init__()
        self.client = LLMClient(
            model=SystemEnv.LLM_NAME,
            api_key=SystemEnv.LLM_APIKEY,
            api_base=SystemEnv.LLM_ENDPOINT
        )

    def expand(self, task_description: str, current_workflow: dict[str, str], round_context: WorkflowLogFormat) -> OptimizeResp:
        # Expand the workflow by adding a new node
        # tools = current_workflow.get("tools")
        actions = current_workflow.get("actions")
        operators = current_workflow.get("operators")
        experts = current_workflow.get("experts")
        
        workflow = f"{operators}\n\n{experts}\n\n"

        prompt = optimize_prompt_template.format(
            task_description=task_description,
            actions=actions,
            current_workflow=workflow,
            score=round_context.score,
            modification=round_context.modification,
            experience=round_context.experience,
            feedbacks=round_context.feedbacks
        )

        messages = [{"role": "user", "content": prompt}]
        times = 0
        obj = None
        while times <= 5: # TODO:
            try:
                response = self.client.generate(messages, response_format=OptimizeResp)
                pattern = r'\{[^{}]*\}'
                resp_str = response.choices[0].message.content
                re.search(pattern, resp_str, re.DOTALL)
                obj = json.loads(resp_str)
                fileds = OptimizeResp.model_fields.keys()
                for filed in fileds:
                    if filed  not in obj:
                        raise Exception(f"{obj} missing {filed}")
                
                return OptimizeResp(
                    modification=obj["modification"],
                    workflow=obj["workflow"]
                )
            except Exception as e:
                print(f"[expand_workflow] failed, reason={e}, times={times}")
                messages.append({
                    "role": "assistant",
                    "content": "response"
                })
                messages.append({
                    "role": "user",
                    "content": f"An error has been encountered, reason={e}. please try generating the workflow again "
                })
            times += 1
        return obj 