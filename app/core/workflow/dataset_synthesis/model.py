from pydantic import BaseModel


class Row(BaseModel):
    task: str
    verifier: str


class WorkflowTrainDataset(BaseModel):
    name: str
    task_desc: str
    dataset: list[Row]