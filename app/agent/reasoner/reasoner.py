from abc import ABC, abstractmethod
from typing import Any


class Rreasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

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
