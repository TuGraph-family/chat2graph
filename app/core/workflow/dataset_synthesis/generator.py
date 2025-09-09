from abc import ABC, abstractmethod
from app.core.toolkit.graph_db.graph_db import GraphDb
from app.core.reasoner.model_service_factory import ModelServiceFactory, ModelService
from app.core.model.message import ModelMessage
from app.core.common.type import MessageSourceType
from app.core.prompt.data_synthesis import generate_query_tv_template, generate_non_query_tv_template, strategy_indentify_template
from app.core.workflow.dataset_synthesis.sampler import SubGraphSampler, SimpleRandomSubGraphSampler
from app.core.workflow.dataset_synthesis.model import Row, WorkflowTrainDataset, GENERATOR_STRATEGY, TASK_TYPES
from app.core.workflow.dataset_synthesis.task_subtypes import GraphTaskTypesInfo
from app.core.common.system_env import SystemEnv
from typing import Type, List, get_args, Dict
import json
import re
import time
import random


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
                 strategy: GENERATOR_STRATEGY = None,
                 sampler_cls: Type[SubGraphSampler] = SimpleRandomSubGraphSampler,
                 max_depth: int = 2,
                 max_noeds: int = 10,
                 max_edges: int = 20,
                 nums_per_subgraph: int = 10
                 ):
        super().__init__()
        self.graph_db = graph_db
        self._llm: ModelService = ModelServiceFactory.create(model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
        self.sampler_cls: Type[SubGraphSampler] = sampler_cls
        self.max_depth = max_depth
        self.max_nodes = max_noeds
        self.max_edges = max_edges
        self.strategy = strategy
        self.nums_per_subgraph = nums_per_subgraph

    def extract_pairs(self, task_type: TASK_TYPES, text: str) -> list[Row]:
        required_fields = Row.model_fields.keys()
        whitelist= ["task_type"]
        pattern = r'\{[^{}]*\}'
        qas = re.findall(pattern, text, re.DOTALL)
        valid_pairs: list[Row] = []
        for qa in qas:
            try:
                # 将匹配到的字符串解析为 JSON
                obj: Dict= json.loads(qa)

                # 验证是否包含Row的所有字段
                valid = True
                for filed in required_fields:
                    if filed in whitelist:
                        continue

                    if filed not in obj:
                        valid = False
                        break

                if valid:
                    obj["task_type"] = task_type
                    valid_pairs.append(
                        Row.model_validate(obj)
                    )
            except Exception as e:
                # 解析失败则跳过
                continue
        
        if len(valid_pairs) == 0:
            print(f"[Warning]generate 0 qa pair, input={text}") # TODO: log方式
        return valid_pairs
    
    async def identify_strategy(self, task_desc: str) -> GENERATOR_STRATEGY:
        if self.strategy != None:
            return self.strategy

        messages: List[ModelMessage]  = []
        found_strategy: GENERATOR_STRATEGY = None
        strategy_types: List[str] = [strategy for strategy in get_args(GENERATOR_STRATEGY) if strategy]
        strategy_pattern = re.compile(r'\b(query|non-query|mixed)\b', flags=re.I)
        prompt = strategy_indentify_template.format(task_desc=task_desc, strategy_list=str(strategy_types))
        job_id = "identify_strategy_job"
        times = 0
        step = 1
        
        message = ModelMessage(
                payload=prompt,
                source_type=MessageSourceType.MODEL, 
                job_id=job_id,
                step=step,
        )
        messages.append(message)
        while times < 3 and found_strategy == None: #TODO
            times += 1
            response = await self._llm.generate(
                sys_prompt="",
                messages=messages
            )

            text = response.get_payload()
            hits = {m.group(0).lower() for m in strategy_pattern.finditer(text)}
            if len(hits) > 1:
                messages.append(
                            ModelMessage(
                                payload=text,
                                source_type=MessageSourceType.ACTOR,
                                job_id=job_id,
                                step=step
                            )
                        )

                step += 1
                messages.append(
                    ModelMessage(
                        payload=f"Find multiple strategy {hits} in your answer. Please re-examine your answer",
                        source_type=MessageSourceType.MODEL,
                        job_id=job_id,
                        step=step
                    )
                )
            elif hits:
                return hits.pop()
    
        return None
    
    async def generate_pairs(self, task_type: TASK_TYPES, task_types_info: GraphTaskTypesInfo, subgraph: str, task_description: str, nums: int) -> list[Row]:
        prompt_template_map = {
            "query": generate_query_tv_template,
            "non-query": generate_non_query_tv_template
        }

        prompt_template = prompt_template_map[task_type]
        prompt = prompt_template.format(
            task_description=task_description, 
            subgraph=subgraph, 
            num_pairs=nums, 
            task_level_info=task_types_info.get_tasks_info(), 
            task_statistic_info=task_types_info.get_count_info()
        )

        job_id = "generate_pairs_job"
        message = ModelMessage(
            payload=prompt,
            source_type=MessageSourceType.MODEL,
            job_id=job_id,
            step=1,
        )

        # 生成响应
        response = await self._llm.generate(
            sys_prompt="",
            messages=[message]
        )

        qas: list[Row] = self.extract_pairs(task_type, response.get_payload())
        return qas
        
    def get_task_type_from_strategy(self, strategy: GENERATOR_STRATEGY) -> TASK_TYPES:
        if strategy == None:
            raise ValueError("strategy is None")
        if strategy != "mixed":
            return strategy

        return random.choice([x for x in get_args(TASK_TYPES) if x])
        
    async def filter(self, pairs: list[Row]) -> list[Row]:
        # TODO: implement
        return pairs
    
    async def generate(self, task_desc: str, dataset_name: str, size: int)->WorkflowTrainDataset:
        dataset: list[Row] = []
        total = 0
        max_times = size // self.nums_per_subgraph + 20 # 生成size个问题，需要 size // nums_per_subgraph 上取整轮，+20来控制最大失败次数
        times = 0

        subgraph_getter: SubGraphSampler = self.sampler_cls()
        strategy: GENERATOR_STRATEGY = await self.identify_strategy(task_desc)

        if strategy == None:
            raise Exception(f"Cann't indentify strategy from task description={task_desc}")

        task_types_info = GraphTaskTypesInfo(
            strategy=strategy
        )

        # 生成数据
        while total < size and times < max_times: 
            # 假设从图数据库获取一个随机节点，并从该节点抽取子图
            times += 1
            try:
                subgraph = subgraph_getter.get_random_subgraph(self.graph_db, max_depth=self.max_depth, max_nodes=self.max_nodes, max_edges=self.max_edges)
                if subgraph == "":
                    raise Exception("get a empty subgraph")
            except Exception as e:
                print(f"[SamplingDatasetGenerator][generate] except while get_random_subgraph, reason={e}")
                continue

            nums = min(self.nums_per_subgraph, size - total)
            task_type = self.get_task_type_from_strategy(strategy=strategy)
            try:
                pairs = await self.generate_pairs(task_type=task_type, task_types_info=task_types_info, subgraph=subgraph, task_description=task_desc, nums=nums)
            except Exception as e:
                print(f"[SamplingDatasetGenerator][generate] except while generate_pairs, reason={e}")
                continue

            pairs = await self.filter(pairs=pairs)

            task_types_info.update(pairs)
            dataset.extend(pairs)
            total += len(pairs)
            time.sleep(2) # 速率控制

        # 创建最终数据集对象
        workflow_dataset = WorkflowTrainDataset(name=dataset_name, task_desc=task_desc, dataset=dataset)

        print(task_types_info.get_count_info())
        return workflow_dataset

    def load(self, task_desc: str, path: str) -> WorkflowTrainDataset:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        dataset: list[Row] = []

        for qa in data:
            dataset.append(
                    Row.model_validate(qa)
            )

        return WorkflowTrainDataset(name="test", task_desc=task_desc, dataset=dataset)
    