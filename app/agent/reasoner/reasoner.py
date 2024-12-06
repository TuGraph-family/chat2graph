from abc import ABC, abstractmethod
from typing import Any, List, Optional
from uuid import uuid4

from app.agent.task import Task
from app.memory.reasoner_memory import ReasonerMemory
from app.toolkit.tool.tool import Tool


class ReasonerCaller(ABC):
    """Reasoner caller.

    Attributes:
        _id (str): The unique identifier of the caller
    """

    def __init__(self, id: str = str(uuid4())):
        self._id: str = id

    @abstractmethod
    def get_id(self) -> str:
        """Get the unique identifier of the caller."""


class Reasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    @abstractmethod
    async def infer(
        self,
        task: Task,
        tools: Optional[List[Tool]] = None,
        caller: Optional[ReasonerCaller] = None,
    ) -> str:
        """Infer by the reasoner."""

    @abstractmethod
    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    @abstractmethod
    async def conclure(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclure the inference results."""

    @abstractmethod
    def init_memory(
        self, task: Task, caller: Optional[ReasonerCaller] = None
    ) -> ReasonerMemory:
        """Initialize the memory."""

    @abstractmethod
    def get_memory(self, task: Task, caller: ReasonerCaller) -> ReasonerMemory:
        """Get the memory."""
