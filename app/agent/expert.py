from abc import ABC, abstractmethod

from app.agent.reasoner.base_reasoner import BaseReasoner
from app.agent.workflow.workflow import Workflow
from app.memory.memory import Memory


class Expert(ABC):
    """An expert is a role that can execute a workflow."""

    def __init__(self, role: str, profile: str, reasoner: BaseReasoner):
        """"""
        self.id: str = None
        self.role: str = role
        self.profile: str = profile
        self.memory: Memory = None
        self.reasoner: BaseReasoner = reasoner

        self.workflow: Workflow = None

        self.task: str = None
        self.input_scrachpad: str = None
        self.input_memory: str = None
        self.input_knowledge: str = None
        self.context: str = None

        # times of calling other/slef expert or leader
        self.called_num: int = 0
        self.max_called_num: int = 3

    @abstractmethod
    async def execute_workflow(self):
        """Execute the workflow."""

    @abstractmethod
    async def call_next(self):
        """Call the next expert."""

    @abstractmethod
    async def call_back(self):
        """Call the privious expert."""

    @abstractmethod
    async def call_leader(self):
        """Call the leader expert."""

    @abstractmethod
    async def analyse_evalution(self):
        """Analyse the evalution of the execution of the workflow."""

    @abstractmethod
    def set_context_propmt(self) -> str:
        """Set the context prompt by combining the input scratchpad, memory and knowledge."""
