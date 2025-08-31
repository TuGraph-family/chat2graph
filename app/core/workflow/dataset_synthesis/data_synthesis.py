from app.core.toolkit.graph_db.graph_db import GraphDb
from abc import ABC, abstractmethod
from pydantic import BaseModel

class Row(BaseModel):
    task: str
    verifier: str

class WorkflowTrainDataset(BaseModel):
    name: str
    task_desc: str
    dataset: list[Row]

class DatasetGenerator(ABC):
    @abstractmethod
    async def generate(self, task_desc: str, dataset_name: str, size: int, **kwargs)->WorkflowTrainDataset:
        ...
    
    @abstractmethod
    def load(self, task_desc: str, path: str) -> WorkflowTrainDataset:
        ...

class SubGraphGetter(ABC):
    @abstractmethod
    def get_random_subgraph(self, graph_db: GraphDb, max_depth: int, max_nodes: int, max_edges: int) -> str:
        ...

