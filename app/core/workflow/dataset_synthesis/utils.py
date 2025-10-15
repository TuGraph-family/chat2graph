import json

from app.core.workflow.dataset_synthesis.model import Row, WorkflowTrainDataset


def load_workflow_train_dataset(task_desc: str, path: str, ratio: float = 1.0) -> WorkflowTrainDataset:
    assert(0 <= ratio <= 1.0 )
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        dataset: list[Row] = []

        for qa in data:
            dataset.append(Row.model_validate(qa))
        return WorkflowTrainDataset(name="test", task_desc=task_desc, data=dataset[:int(len(dataset) * ratio)])
