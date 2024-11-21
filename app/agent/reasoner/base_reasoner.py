from abc import ABC, abstractmethod
from typing import Any, List

from app.toolkit.tool.tool import Tool


class BaseReasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    @abstractmethod
    async def infer(
        self,
        op_id: str,
        task: str,
        func_list: List[Tool] = None,
        reasoning_rounds: int = 5,
        print_messages: bool = False,
    ):
        """Infer by the reasoner."""

    @abstractmethod
    async def update_knowledge(self, data: Any):
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self):
        """Evaluate the inference process."""

    @abstractmethod
    async def conclure(self):
        """Conclure the inference results."""
