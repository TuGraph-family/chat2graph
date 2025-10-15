from abc import abstractmethod


class WorkflowGenerator:
    @abstractmethod
    def generate(self) -> str: ...
