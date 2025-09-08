from pydantic import BaseModel
from typing import Literal, Dict, List, get_args

TASK_TYPES = Literal["query", "non-query"] # 描述了生成的具体的tv对的类型
GENERATOR_STRATEGY = Literal["query", "non-query", "mixed", None] # 描述generator需要生成的数据集是纯query， non-query 还是 混合mixed的
TASK_LEVEL = Literal["L1", "L2", "L3", "L4"] 


class Row(BaseModel):
    level: TASK_LEVEL
    task_type: TASK_TYPES
    task_subtype: str
    task: str
    verifier: str


class WorkflowTrainDataset(BaseModel):
    name: str
    task_desc: str
    dataset: list[Row]


class SubTaskType(BaseModel):
    level: TASK_LEVEL
    name: str
    desc: str
    examples: list[str]

class LevelInfo(BaseModel):
    level: TASK_LEVEL
    name: str
    desc: str
    subtasks: List[SubTaskType]