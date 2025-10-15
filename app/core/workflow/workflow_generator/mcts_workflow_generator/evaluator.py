from abc import abstractmethod
import io
import json
from pathlib import Path
import sys
from typing import Dict, List, Tuple

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import HybridMessage, ModelMessage, TextMessage
from app.core.prompt.workflow_generator import eval_prompt_template, reflect_prompt_template
from app.core.reasoner.model_service_factory import ModelService, ModelServiceFactory
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.workflow.dataset_synthesis.model import Row
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import (
    ExecuteResult,
    ReflectResult,
)
from app.core.workflow.workflow_generator.mcts_workflow_generator.utils import (
    JsonValue,
    generate_json,
    load_agentic_service,
    load_execute_result,
)


class Evaluator:
    @abstractmethod
    async def evaluate_workflow(
        self,
        optimized_path: str,
        round_num: int,
        parent_round: int,
        dataset: List[Row],
        modifications: List[str],
    ) -> Tuple[float, str]: ...


class LLMEvaluator(Evaluator):
    def __init__(self, need_reflect = True):
        super().__init__()
        self._llm: ModelService = ModelServiceFactory.create(
            model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE
        )
        self.job_id = "[LLMEvaluator]"
        self.need_reflect = need_reflect

    async def evaluate_workflow(
        self,
        optimized_path: str,
        round_num: int,
        parent_round: int,
        dataset: List[Row],
        modifications: List[str],
    ) -> Tuple[float, str]:
        save_dir = Path(optimized_path) / f"round{round_num}"
        save_dir.mkdir(parents=True, exist_ok=True)
        results_file = save_dir / "results.json"
        if parent_round > 0:
            parent_dir = Path(optimized_path) / f"round{parent_round}"
            parent_results_file = parent_dir / "results.json"
            parent_results = load_execute_result(parent_results_file)
            parent_scores = {result.task: result.score for result in parent_results}
        else:
            parent_scores = {}

        total_score = 0.0
        results: List[ExecuteResult] = []
        try:
            agent_sys = load_agentic_service(
                optimized_path=optimized_path, round_num=round_num
            )  
        except Exception as e:
            results.append(
                ExecuteResult(
                    task="",
                    verifier="",
                    model_output="",
                    ori_score=-1,
                    score=-1,
                    error=f"load_agentic_service failed, the configuration file has errors, reason={e}",  # noqa: E501
                    succeed="no",
                )
            )
            
            agent_sys = None
            
        class Blackhole:
            def write(self, *args, **kwargs):
                pass  # 吃掉所有写入的数据，什么也不做
            
            def flush(self):
                pass  # 有些库会调用 flush，也需要处理
        if agent_sys is not None:
            original_stdout = sys.stdout
            f = io.StringIO()
            sys.stdout = Blackhole()
            step_size = len(dataset)
            for start in range(0, len(dataset), step_size):
                jobs: List[tuple[Row, JobWrapper]] = []
                batch = dataset[start:start + step_size]
                for data in batch:
                    result = None
                    message = TextMessage(
                        payload=data.task,
                    )
                    jobs.append((data, agent_sys.session().submit(message)))
                        

                for data, jobwrapper in jobs:
                    f.flush()
                    try:
                        parent_score = parent_scores.get(data.task, -1)
                        model_message = jobwrapper.wait()
                        if isinstance(model_message, TextMessage):
                            result = model_message.get_payload()
                        elif isinstance(model_message, HybridMessage):
                            result = model_message.get_instruction_message().get_payload()

                        score = await self._llm_scoring(
                            question=data.task, model_output=str(result), expected_answer=data.verifier # TODO: async tasks
                        )
                        
                        total_score += score
                        succeed = "unknown"
                        if parent_score < 0:
                            succeed = "unknown"
                        elif score > parent_score:
                            succeed = "yes"
                        else:
                            succeed = "no"

                        results.append(
                            ExecuteResult(
                                task=data.task,
                                verifier=data.verifier,
                                model_output=str(result),
                                ori_score=parent_score,
                                score=score,
                                error="",
                                succeed=succeed,
                            )
                        )
                    except Exception as e:
                        results.append(
                            ExecuteResult(
                                task=data.task,
                                verifier=data.verifier,
                                model_output=str(result),
                                ori_score=parent_score,
                                score=0,
                                error=f"{e}",
                                succeed="no",
                            )
                        )
                    
            sys.stdout = original_stdout

        avg_score = total_score / len(dataset)
        with open(results_file, "w", encoding="utf-8") as f:
            # result = [{"avg_score": avg_score}]
            # result.extend()
            json.dump([result.model_dump() for result in results], f, ensure_ascii=False, indent=2)

        if self.need_reflect:
            reflect_reuslt = await self._reflect(
                modifications=modifications, results=results, avg_score=avg_score
            )
        else:
            reflect_reuslt = ReflectResult(
                failed_reason=[],
                optimize_suggestion=[]
            )

        return avg_score, reflect_reuslt.model_dump_json(indent=2)

    async def _pack_infer_trace(
        self, modifications: List[str], results: List[Dict[str, str]], avg_score: float
    ):  # [action1, reason1, observe1, ..., action_n, reason_n, observe_n,...]
        # todo: action对应Modification, observe对应results和avg_score，需要用LLM归因，推出action的motivation，插入到action和observe之间  # noqa: E501
        # List[InferTrace], Infertace =(a, r, o)
        ...

    async def _reflect(
        self, modifications: List[str], results: List[ExecuteResult], avg_score: float
    ) -> ReflectResult:
        prompt = reflect_prompt_template.format(
            modification=modifications,
            results=json.dumps(
                [result.model_dump() for result in results], ensure_ascii=False, indent=2
            ),
        )
        messages = [
            ModelMessage(
                payload=prompt,
                job_id=self.job_id,
                step=1,
                source_type=MessageSourceType.MODEL,
            )
        ]

        def checker(results: List[JsonValue]) -> JsonValue:
            fileds = ReflectResult.model_fields.keys()
            for result in results:
                if isinstance(result, dict):
                    for field in fileds:
                        if field not in result:
                            raise Exception(f"missing {field} in {result}")
                    return result
                else:
                    raise Exception("output must be a dict")
            return None

        resp = await generate_json(
            model=self._llm,
            sys_prompt="",
            messages=messages,
            filter=checker,
        )
        return ReflectResult.model_validate(resp)

    async def _llm_scoring(self, question: str, model_output: str, expected_answer: str) -> int:
        prompt = eval_prompt_template.format(
            question=question, expected_answer=expected_answer, model_output=model_output
        )
        messages = [
            ModelMessage(
                payload=prompt,
                job_id=self.job_id,
                step=1,
                source_type=MessageSourceType.MODEL,
            )
        ]

        def filter(results: List[JsonValue]) -> JsonValue:
            for result in results:
                if isinstance(result, dict):
                    if "score" not in result:
                        raise Exception(f"missing score field in {result}")
                    return result["score"]
                else:
                    raise Exception("output must be a json dict")

            return None

        resp = await generate_json(
            model=self._llm,
            sys_prompt="",
            messages=messages,
            filter=filter,
        )

        if isinstance(resp, int):
            return resp
        else:
            return 0
