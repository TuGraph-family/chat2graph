from abc import ABC, abstractmethod
from app.core.toolkit.graph_db.graph_db import GraphDb
from app.core.reasoner.model_service_factory import ModelServiceFactory, ModelService
from app.core.model.message import ModelMessage
from app.core.common.type import MessageSourceType
from app.core.prompt.data_synthesis import synthesis_prompt_template
from app.core.workflow.dataset_synthesis.sampler import SubGraphSampler, SimpleRandomSubGraphSampler, EnhancedSubgraphSampler
from app.core.workflow.dataset_synthesis.model import Row, WorkflowTrainDataset
from app.core.common.system_env import SystemEnv
from typing import Type
import json
import re
import time


class DatasetGenerator(ABC):
    @abstractmethod
    async def generate(self, task_desc: str, dataset_name: str, size: int)->WorkflowTrainDataset:
        ...

    @abstractmethod
    def load(self, task_desc: str, path: str) -> WorkflowTrainDataset:
        ...


class SamplingDatasetGenerator(DatasetGenerator):
    def __init__(self, 
                 graph_db: GraphDb, 
                 sampler_cls: Type[SubGraphSampler] = SimpleRandomSubGraphSampler,
                 max_depth: int = 2,
                 max_noeds: int = 10,
                 max_edges: int = 20,
                 ):
        super().__init__()
        self.graph_db = graph_db
        self._llm: ModelService = ModelServiceFactory.create(model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
        self.sampler_cls: Type[SubGraphSampler] = sampler_cls
        self.max_depth = max_depth
        self.max_nodes = max_noeds
        self.max_edges = max_edges

    async def generate_pairs(self, subgraph: str, task_description: str, nums: int) -> list[Row]:
        prompt = synthesis_prompt_template.format(task_description=task_description, subgraph=subgraph, num_pairs=nums)
        job_id = "generate_pairs_job"
        messages = ModelMessage(
            payload=prompt,
            source_type=MessageSourceType.THINKER,
            job_id=job_id,
            step=1,
        )

        # 生成响应
        response = await self._llm.generate(
            sys_prompt="",
            messages=[messages]
        )

        qas: list[Row] = self.extract_tvs(response.get_payload())
        return qas

    def extract_tvs(self, text: str) -> list[Row]:
        required_fields = Row.model_fields.keys()
        pattern = r'\{[^{}]*\}'
        qas = re.findall(pattern, text, re.DOTALL)
        valid_pairs: list[Row] = []
        for qa in qas:
            try:
                # 将匹配到的字符串解析为 JSON
                obj = json.loads(qa)

                # 验证是否包含Row的所有字段
                valid = True
                for filed in required_fields:
                    if filed not in obj:
                        valid = False
                        break

                if valid:
                    valid_pairs.append(obj)
            except Exception as e:
                # 解析失败则跳过
                continue
        
        if len(valid_pairs) == 0:
            print(f"[Warning]generate 0 qa pair, input={text}") # TODO: log方式
        return valid_pairs

    async def generate(self, task_desc: str, dataset_name: str, size: int)->WorkflowTrainDataset:
        dataset: list[Row] = []
        nums_per_subgraph = 10

        total = 0
        max_times = size // nums_per_subgraph + 20 # 生成size个问题，需要 size // nums_per_subgraph 上取整轮，+20来控制最大失败次数
        times = 0
        subgraph_getter: SubGraphSampler = self.sampler_cls()
        # 生成数据
        while total < size and times < max_times: 
            # 假设从图数据库获取一个随机节点，并从该节点抽取子图
            subgraph = subgraph_getter.get_random_subgraph(self.graph_db, max_depth=self.max_depth, max_nodes=self.max_nodes, max_edges=self.max_edges)# TODO: 抽象

            nums = min(nums_per_subgraph, size - total)
            # 基于任务描述和子图生成查询和期望输出
            paris = await self.generate_pairs(subgraph=subgraph, task_description=task_desc, nums=nums)

            dataset.extend(paris)

            total += len(paris)
            times += 1
            time.sleep(5) # 速率控制

        # 创建最终数据集对象
        workflow_dataset = WorkflowTrainDataset(name=dataset_name, task_desc=task_desc, dataset=dataset)

        return workflow_dataset

    def load(self, task_desc: str, path: str) -> WorkflowTrainDataset:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset: list[Row] = []

        for qa in data:
            dataset.append(
                    Row(
                        task=qa["task"],
                        verifier=qa["verifier"]
                        )
            )

        return WorkflowTrainDataset(name="test", task_desc=task_desc, dataset=dataset)
    