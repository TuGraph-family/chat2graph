from abc import abstractmethod


class WorkflowGenerator:
    def __init__(self, init_workflow: str):
        self.init_workflow = init_workflow
        pass

    @abstractmethod
    def generate(self) -> str: ...
