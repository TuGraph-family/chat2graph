from abc import ABC

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

    async def execute_workflow(self):
        """Execute the workflow."""

    async def evaluate_workflow(self):
        """Evaluate the workflow."""

    async def auto_plan(self):
        """Auto plan the subtasks and auto call the agents"""

    async def _call_next(self):
        """Call the next expert."""

    async def _call_back(self):
        """Call the privious expert."""

    async def _call_leader(self):
        """Call the leader expert."""

    async def _analyse_evalution(self):
        """Analyse the evalution of the execution of the workflow."""

    def set_context_propmt(self) -> str:
        """Set the context prompt by combining the input scratchpad, memory and knowledge."""
