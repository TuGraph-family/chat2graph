from abc import ABC, abstractmethod
from typing import Any


class KnowledgeService(ABC):
    """Knowledge base service."""

    # TODO: the following methods are not implemented yet

    @abstractmethod
    def query(self, query: Any) -> Any:
        """Execute a knowledge query."""

    @abstractmethod
    def get_knowledge(self, *args, **kwargs) -> Any:
        """Get knowledge by ID."""

    @abstractmethod
    def update_knowledge(self, *args, **kwargs) -> Any:
        """Update existing knowledge entry."""

    @abstractmethod
    def delete_knowledge(self, *args, **kwargs) -> Any:
        """Delete knowledge entry."""
