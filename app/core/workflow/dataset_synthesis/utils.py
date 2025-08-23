import json

from app.core.workflow.dataset_synthesis.model import Row, WorkflowTrainDataset


def load_workflow_train_dataset(task_desc: str, path: str) -> WorkflowTrainDataset:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        dataset: list[Row] = []

        for qa in data:
            dataset.append(Row.model_validate(qa))
        return WorkflowTrainDataset(name="test", task_desc=task_desc, dataset=dataset)
