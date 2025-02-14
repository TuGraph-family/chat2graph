from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.task import Task


class Reasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    def __init__(self):
        self._memories: Dict[str, Dict[str, Dict[str, ReasonerMemory]]] = {}

    @abstractmethod
    async def infer(self, task: Task) -> str:
        """Infer by the reasoner."""

    @abstractmethod
    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    @abstractmethod
    async def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclude the inference results."""

    @abstractmethod
    def init_memory(self, task: Task) -> ReasonerMemory:
        """Initialize the memory."""

    @abstractmethod
    def get_memory(self, task: Task) -> ReasonerMemory:
        """Get the memory."""
