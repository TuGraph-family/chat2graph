from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.agent.task import Task
from app.memory.memory import Memory
from app.toolkit.tool.tool import Tool


class ReasonerCaller(ABC):
    """Reasoner caller.

    Attributes:
        _caller_id (str): The unique identifier of the caller
    """

    def __init__(self, caller_id: Optional[str] = None):
        self._caller_id: str = caller_id

    @abstractmethod
    def get_caller_id(self) -> str:
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
    async def conclure(self, memory: Memory) -> str:
        """Conclure the inference results."""

    @abstractmethod
    def init_memory(
        self, task: Task, caller: Optional[ReasonerCaller] = None
    ) -> Memory:
        """Initialize the memory."""

    @abstractmethod
    def get_memory(self, task: Task, caller: ReasonerCaller) -> Memory:
        """Get the memory."""
