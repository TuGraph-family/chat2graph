from abc import ABC, abstractmethod
from typing import Any, List
from app.core.model.knowledge import KnowledgeChunk


class KnowledgeStore(ABC):
    """Knowledge store for storing docs, vectors, graphs."""

    @abstractmethod
    def __init__(self, name):
        """Init knowledge store."""

    @abstractmethod
    def load_document(self, file_path) -> List[str]:
        """Load document."""

    @abstractmethod
    def delete_document(self, chunk_ids):
        """Delete document."""

    @abstractmethod
    def update_document(self, file_path, chunk_ids) -> List[str]:
        """Update document."""

    @abstractmethod
    def retrieve(self, query) -> KnowledgeChunk:
        """retrieve knowledge from knowledge store."""

    @abstractmethod
    def clear(self):
        """clear all knowledge in knowledge store."""

    @abstractmethod
    def drop(self):
        """drop the entire knowledge store persistance data."""
