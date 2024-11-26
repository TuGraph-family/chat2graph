from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.toolkit.tool.tool import Tool


class Reasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    @abstractmethod
    async def infer(
        self,
        op_id: str,
        task: str,
        func_list: Optional[List[Tool]] = None,
        reasoning_rounds: int = 5,
        print_messages: bool = False,
    ) -> str:
        """Infer by the reasoner."""

    @abstractmethod
    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    @abstractmethod
    async def conclure(self, op_id: str) -> str:
        """Conclure the inference results."""
