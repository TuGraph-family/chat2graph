from app.core.workflow.dataset_synthesis.model import Row
from app.core.prompt.workflow_generator import init_template, eval_prompt_template, summary_prompt_template, optimize_prompt_template
from app.core.workflow.dataset_synthesis.model import WorkflowTrainDataset
from app.core.workflow.workflow_generator.llm_client import LLMClient
from app.core.service.graph_db_service import GraphDb
from app.core.common.system_env import SystemEnv
from app.core.workflow.workflow_generator.mcts_workflow_generator.model import WorkflowLogFormat
from app.core.workflow.workflow_generator.mcts_workflow_generator.selector import Selector
from app.core.workflow.workflow_generator.mcts_workflow_generator.expander import Expander
from app.core.workflow.workflow_generator.mcts_workflow_generator.evaluator import Evaluator
import random
from pathlib import Path
import re
import json
import time 


class MCTSWorkflowGenerator:
    def __init__(self, 
                 db: GraphDb,
                 dataset: WorkflowTrainDataset,
                 selector: Selector,
                 expander: Expander,
                 evaluator: Evaluator,
                 max_rounds: int = 30, 
                 validate_rounds: int = 5,
                 optimized_path: str = "workflow_space",
                 sample_size: int = 5,
                 max_retries: int = 5,
                ):
        self.dataset = dataset
        self.db:GraphDb = db
        self.selector: Selector = selector
        self.expander: Expander = expander
        self.evaluator: Evaluator = evaluator
        
        self.max_rounds = max_rounds
        self.validate_rounds = validate_rounds
        self.optimized_path =  f"{optimized_path}/{self.dataset.name}_{str(int(time.time()))}"
        self.sample_size = sample_size
        self.max_retries = max_retries
        self.logs: dict[int, WorkflowLogFormat] = {}


        self.client = LLMClient(
            model=SystemEnv.LLM_NAME,
            api_key=SystemEnv.LLM_APIKEY,
            api_base=SystemEnv.LLM_ENDPOINT
        )
    
    def init_workflow(self):
        """
        Initialize a default workflow.py based on a template, and save it to optimized_path.
        """

        # 创建保存路径
        save_path = Path(self.optimized_path) / "round1"
        save_path.mkdir(parents=True, exist_ok=True)

        # 写入 workflow.py 文件
        workflow_file = save_path / "workflow.yml"
        with open(workflow_file, "w", encoding="utf-8") as f:
            f.write(init_template)

        print(f"Initialized default workflow at: {workflow_file}")
    
    def split_dataset(self, test_size: float = 0.5, random_state: int = 42) -> tuple[list[Row], list[Row]]:
        """Split the dataset into training and validation sets."""
        data = self.dataset.dataset
        random.seed(random_state)
        random.shuffle(data)
        split_index = int(test_size * len(data))
        train_data = data[split_index:]
        test_data = data[:split_index]
        return train_data, test_data
    
    def load_workflow_dict(self, round_num) -> dict[str, str]:
        workflow_path = self.optimized_path + f"/round{round_num}" + "/workflow.yml"
        try:
            with open(workflow_path, 'r', encoding='utf-8') as file:
                content = file.read()

            sections = ("app", "plugin", "reasoner", "tools", "toolkit", "actions", "operators", "experts", "knowledgebase", "memory", "env")
            results = {}
            for section in sections:
                # 匹配某个 key 到下一个顶级 key 或文件末尾
                pattern = re.compile(
                    rf"(^|\n){section}:(.*?)(?=\n\w+:|\Z)", 
                    re.DOTALL
                )
                match = pattern.search(content)
                if match:
                    results[section] = match.group(0).strip()

            return results
        except FileNotFoundError:
            print(f"文件未找到: {workflow_path}")
            return ""
        except Exception as e:
            print(f"读取文件时发生错误: {e}")
            return ""

    def update_parent_feedbacks(self, parent_round, current_round):
        self.logs[parent_round].feedbacks.append(
            {
                "round_number": self.logs[current_round].round_number,
                "score": self.logs[current_round].score,
                "modification": self.logs[current_round].modification,
                "experience": self.logs[current_round].experience,
            }
        )
        
    def log_save(self):
        save_dir = Path(self.optimized_path) / "log"
        save_dir.mkdir(parents=True, exist_ok=True)
        log_file = save_dir / "log.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump([v.model_dump(mode="json") for k, v in self.logs.items()], f, ensure_ascii=False, indent=2)

    def run(self):
        train_data, test_data = self.split_dataset()

        # init
        print("[run]init_workflow...")
        self.init_workflow()
        score, experience = self.evaluator.evaluate_workflow(round_num=1, dataset=test_data, modification="", optimized_path=self.optimized_path)
        self.logs[1] = WorkflowLogFormat(round_number=1, score=score, experience=experience, modification="None", feedbacks=[])
        # self.logs[1] = WorkflowLogFormat(round_number=1, score=1, experience="None", modification="None", feedbacks=[])

        for round_num in range(2, self.max_rounds+1):
            print(f"[run]optimize, round={round_num}...")
            # Select a workflow
            select_retry_times = 0
            while select_retry_times < self.max_retries:
                select_retry_times += 1
                select_round = self.selector.select(sample_size=self.sample_size, logs=self.logs)
                round_context = self.logs.get(select_round.round_number, None)
                if round_context != None:
                    break
            
            # Load Workflow
            workflow = self.load_workflow_dict(select_round.round_number)

            # Expand the workflow
            new_flow = self.expander.expand(task_description=self.dataset.task_desc, current_workflow=workflow, round_context=round_context)

            if new_flow == None:
                print(f"[run]new flow generate failed, round={round_num}")
                continue

            # Save workflow
            new_flow_dir = Path(self.optimized_path + f"/round{round_num}")
            new_flow_dir.mkdir(parents=True, exist_ok=True)
            new_flow_path = new_flow_dir / "workflow.yml"
            try:
                with open(new_flow_path, 'w', encoding='utf-8')  as f:
                    sections = ("app", "plugin", "reasoner", "tools", "actions",  "toolkit")
                    for section in sections:
                        f.write(workflow.get(section, ""))
                        f.write("\n\n")
                    f.write(new_flow.workflow)
                    f.write("\n\n")
                    sections = ("knowledgebase", "memory", "env")
                    for section in sections:
                        f.write(workflow.get(section, ""))
                        f.write("\n\n")
            except Exception as e:
                print(f"[run]exception while saving workflow")
                continue

            # Evaluate the new node
            score, experience = self.evaluator.evaluate_workflow(
                round_num=round_num, 
                dataset=train_data, 
                modification=new_flow.modification,
                optimized_path=self.optimized_path
                )

            # save result
            self.logs[round_num] = WorkflowLogFormat(round_number=round_num, score=score, experience=experience, modification=new_flow.modification, feedbacks=[])

            # update exprience for father node
            self.update_parent_feedbacks(select_round.round_number, round_num)

        # TODO: 选出最优的

    
