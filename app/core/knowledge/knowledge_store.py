from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.knowledge.knowledge_config import KnowledgeConfig
from app.core.model.knowledge import KnowledgeChunk


class KnowledgeStore(ABC):
    """Knowledge store for storing docs, vectors, graphs."""

    @abstractmethod
    def __init__(self, name: str):
        """Init knowledge store."""

    @abstractmethod
    def load_document(self, file_path: str, config: Optional[KnowledgeConfig]) -> str:
        """Load document."""

    @abstractmethod
    def delete_document(self, chunk_ids: str) -> None:
        """Delete document."""

    @abstractmethod
    def update_document(self, file_path: str, chunk_ids: str) -> str:
        """Update document."""

    @abstractmethod
    def retrieve(self, query: str) -> List[KnowledgeChunk]:
        """retrieve knowledge from knowledge store."""

    @abstractmethod
    def drop(self) -> None:
        """drop the entire knowledge store persistance data."""
