from abc import abstractmethod
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import OptimizeResp, WorkflowLogFormat, Score
from app.core.workflow.dataset_synthesis.data_synthesis import Row
from app.core.prompt.workflow_generator import summary_prompt_template, optimize_prompt_template, eval_prompt_template
from app.core.model.message import TextMessage, HybridMessage
from app.core.common.system_env import SystemEnv
from app.core.workflow.workflow_generator.llm_client import LLMClient
from app.core.workflow.workflow_generator.mcts_workflow_generator.utils import load_workflow
import json
import sys
import io
import re
from pathlib import Path

class Evaluator:
    @abstractmethod
    def evaluate_workflow(self, round_num: int, dataset: list[Row], modification: str, optimized_path: str) ->  tuple[float, str]:
        ...

class LLMEvaluator(Evaluator):
    def __init__(self):
        super().__init__()
        self.client = LLMClient(
            model=SystemEnv.LLM_NAME,
            api_key=SystemEnv.LLM_APIKEY,
            api_base=SystemEnv.LLM_ENDPOINT
        )
    
    def evaluate_workflow(self, round_num: int, dataset: list[Row], modification: str, optimized_path: str) ->  tuple[float, str]:
        total_score = 0.0
        results: dict[str, str] = []
        try :
            workflow = load_workflow(optimized_path=optimized_path, round_num=round_num) 
            for qa in dataset:
                try:
                    result = None
                    message = TextMessage(
                        payload=qa.task,
                        assigned_expert_name=None
                    )

                    original_stdout = sys.stdout
                    f = io.StringIO()
                    sys.stdout = f
                    model_message = workflow.session().submit(message).wait()
                    sys.stdout = original_stdout

                    if isinstance(model_message, TextMessage):
                        result = model_message.get_payload()
                    elif isinstance(model_message, HybridMessage):
                        result = model_message.get_instruction_message().get_payload()
                    score = self.llm_scoring(question=qa.task, workflow_output=result, expected_answer=qa.verifier)
                    total_score += score
                    results.append({
                        "question": qa.task,
                        "model_output": result,
                        "real_anwser": qa.verifier,
                        "score": score,
                        "error": None,
                    })
                except Exception as e:
                    results.append({
                        "question": qa.task,
                        "model_output": result or None,
                        "real_anwser": qa.verifier,
                        "score": 0,
                        "error": f"{e}"
                    })
        except Exception as e:
            results.append({
                    "question": "",
                    "model_output": "",
                    "real_anwser": "",
                    "score": 0,
                    "error": f"{e}"
            })
        
        
        save_dir = Path(optimized_path) / f"round{round_num}"
        save_dir.mkdir(parents=True, exist_ok=True)
        results_file = save_dir / "results.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        avg_score = total_score / len(dataset)
        experience_summary = self.summarize_experience(modification=modification, results=results, avg_score=avg_score)
        return avg_score, experience_summary

    def summarize_experience(self, modification, results, avg_score):
        prompt = summary_prompt_template.format(modification=modification, results=results, avg_score=avg_score)
        messages = [{"role": "user", "content": prompt}]
        experience = self.client.generate(messages)
        return experience.choices[0].message.content

    def llm_scoring(self, question, workflow_output, expected_answer)->int:
        prompt = eval_prompt_template.format(question=question, expected_answer=expected_answer, workflow_output=workflow_output)
        messages = [{"role": "user", "content": prompt}]
        response = self.client.generate(messages, response_format=Score)
        pattern = r'\{[^{}]*\}'
        score = re.search(pattern, response.choices[0].message.content, re.DOTALL)
        try:
            score_obj = json.loads(score.group(0))
            return score_obj["score"]
        except Exception as e:
            raise e