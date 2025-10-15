import json
from pathlib import Path
import random
import shutil
import time
from typing import Dict, List, Tuple

from app.core.service.graph_db_service import GraphDb
from app.core.workflow.dataset_synthesis.model import Row, WorkflowTrainDataset
from app.core.workflow.workflow_generator.mcts_workflow_generator.evaluator import Evaluator
from app.core.workflow.workflow_generator.mcts_workflow_generator.expander import Expander
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import (
    AgenticConfigSection,
    WorkflowLogFormat,
)
from app.core.workflow.workflow_generator.mcts_workflow_generator.selector import Selector
from app.core.workflow.workflow_generator.mcts_workflow_generator.utils import load_config_dict


class MCTSWorkflowGenerator:
    def __init__(
        self,
        db: GraphDb,
        dataset: WorkflowTrainDataset,
        selector: Selector,
        expander: Expander,
        evaluator: Evaluator,
        optimize_grain: List[AgenticConfigSection],
        init_template_path: str = "app/core/workflow/workflow_generator/mcts_workflow_generator/init_template/basic_template.yml",
        max_rounds: int = 30,
        # validate_rounds: int = 5,
        optimized_path: str = "workflow_space",
        top_k: int = 5,
        max_retries: int = 5,
    ):
        if optimize_grain is None:
            optimize_grain = [AgenticConfigSection.EXPERTS, AgenticConfigSection.OPERATORS]
        self.dataset = dataset
        self.db: GraphDb = db
        self.selector: Selector = selector
        self.expander: Expander = expander
        self.evaluator: Evaluator = evaluator

        self.max_rounds = max_rounds
        # self.validate_rounds = validate_rounds
        self.optimized_path = f"{optimized_path}/{self.dataset.name}_{str(int(time.time()))}"
        self.top_k = top_k
        self.max_retries = max_retries
        self.logs: dict[int, WorkflowLogFormat] = {}
        self.optimize_grain = optimize_grain
        self.init_template_path = init_template_path
        self.init_config_dict: Dict[str, str] = {}
        self.max_score = -1
        self.optimal_round = 0

    def init_workflow(self):
        """
        Initialize a default workflow.py based on a template, and save it to optimized_path.
        """

        # 创建保存路径
        save_path = Path(self.optimized_path) / "round1"
        save_path.mkdir(parents=True, exist_ok=True)

        # 写入 workflow.py 文件
        workflow_file = save_path / "workflow.yml"
        shutil.copy2(self.init_template_path, workflow_file)

        print(f"Initialized default workflow at: {workflow_file}")

        config_dict = self.load_config_dict(round_num=1, skip_section=None)
        for section in AgenticConfigSection:
            section_name = str(section.value)
            section_context = config_dict.get(section_name)
            if section_context is None:
                print(
                    f"[MCTSWorkflowGenerator][init_workflow] Cann't find {section_name} in  {workflow_file}"
                )
                continue
            if section not in self.optimize_grain:
                self.init_config_dict[section_name] = section_context

    def split_dataset(
        self, test_size: float = 0.5, random_state: int = 42
    ) -> Tuple[List[Row], List[Row]]:
        """Split the dataset into training and validation sets."""
        data = self.dataset.data
        random.seed(random_state)
        random.shuffle(data)
        split_index = int(test_size * len(data))
        train_data = data[split_index:]
        test_data = data[:split_index]
        return train_data, test_data

    def load_config_dict(
        self, round_num: int, skip_section: List[AgenticConfigSection]
    ) -> Dict[str, str]:
        if skip_section is None:
            skip_section = []
        workflow_path = self.optimized_path + f"/round{round_num}" + "/workflow.yml"
        return load_config_dict(workflow_path, skip_section=skip_section)

    def update_parent_feedbacks(self, parent_round, current_round):
        self.logs[parent_round].feedbacks.append(
            {
                "modification": self.logs[current_round].modifications,
                "after_score": self.logs[current_round].score,
                "reflection": self.logs[current_round].reflection,
                "succeed": self.logs[current_round].score > self.logs[parent_round].score,
            }
        )

    def log_save(self):
        save_dir = Path(self.optimized_path) / "log"
        save_dir.mkdir(parents=True, exist_ok=True)
        log_file = save_dir / "log.json"
        config_file = save_dir / "config.json"
        with open(log_file, "w", encoding="utf-8") as f:
            logs = [v.model_dump(mode="json") for k, v in self.logs.items()]
            json.dump(
                logs,
                f,
                ensure_ascii=False,
                indent=2,
            )

        with open(config_file, "w", encoding = "utf-8") as f:
            config = [
                {
                    "max_rounds": self.max_rounds,
                    "top_k": self.top_k,
                    "init_template_path": self.init_template_path,
                    "max_score": self.max_score,
                    "optimal_round": self.optimal_round,
                }
            ]
            json.dump(
                config,
                f,
                ensure_ascii=False,
                indent=2
            ) 
            
    async def run(self):
        train_data, test_data = self.split_dataset()

        # init
        print("[run]init_workflow...")
        self.init_workflow()
        score, reflection = await self.evaluator.evaluate_workflow(
            round_num=1,
            parent_round=-1,
            dataset=self.dataset.data,
            modifications=[],
            optimized_path=self.optimized_path,
        )
        self.logs[1] = WorkflowLogFormat(
            round_number=1, score=score, reflection=reflection, modifications=[], feedbacks=[]
        )
        # self.logs[1] = WorkflowLogFormat(round_number=1, score=1, experience="None", modification=[], feedbacks=[])
        self.log_save()
        for round_num in range(2, self.max_rounds + 1):
            print(f"[run]optimize, round={round_num}...")
            # Select a workflow
            select_retry_times = 0
            while select_retry_times < self.max_retries:
                select_retry_times += 1
                select_round = self.selector.select(top_k=self.top_k, logs=self.logs)
                round_context = self.logs.get(select_round.round_number, None)
                if round_context is not None:
                    break

            # Load Workflow
            current_config = self.load_config_dict(select_round.round_number, skip_section=[])

            # Expand the workflow
            optimize_suggestions, optimize_resp = await self.expander.expand(
                task_tesc=self.dataset.task_desc,
                current_config=current_config,
                round_context=round_context,
            )

            if optimize_resp is None:
                print(f"[run]new flow generate failed, round={round_num}")
                continue

            # Save workflow
            new_flow_dir = Path(self.optimized_path + f"/round{round_num}")
            new_flow_dir.mkdir(parents=True, exist_ok=True)
            new_flow_path = new_flow_dir / "workflow.yml"
            try:
                with open(new_flow_path, "w", encoding="utf-8") as f:
                    for section in AgenticConfigSection:
                        if section not in self.optimize_grain:
                            section = str(section.value)
                            section_init_context = self.init_config_dict.get(section, None)
                            if section_init_context is None:
                                print(
                                    f"[MCTSWorkflowGenerator][run] Cann't find {section} in init_config_dict"  # noqa: E501
                                )
                                continue
                            f.write(section_init_context)
                            f.write("\n\n")
                    for _, section_context in optimize_resp.new_configs.items():
                        f.write(section_context)
                        f.write("\n\n")
            except Exception:
                print("[run]exception while saving workflow")
                continue

            # Evaluate the new node
            score, reflection = await self.evaluator.evaluate_workflow(
                round_num=round_num,
                dataset=train_data,
                modifications=optimize_resp.modifications,
                optimized_path=self.optimized_path,
                parent_round=select_round.round_number,
            )

            # save result
            self.logs[round_num] = WorkflowLogFormat(
                round_number=round_num,
                score=score,
                reflection=reflection,
                modifications=optimize_resp.modifications,
                feedbacks=[],
                optimize_suggestions=optimize_suggestions,
            )

            # update exprience for father node
            self.update_parent_feedbacks(select_round.round_number, round_num)
            
            if self.logs[round_num].score > self.max_score:
                self.max_score = self.logs[round_num].score
                self.optimal_round = round_num
            self.log_save()

        return self.max_score, self.optimal_round