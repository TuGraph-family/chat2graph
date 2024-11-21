from abc import ABC, abstractmethod
from typing import Any


class Reasoner(ABC):
    """Reasoner is a basic element of the agent."""

    @abstractmethod
    async def infer(self):
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
