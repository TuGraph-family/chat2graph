from abc import ABC, abstractmethod
from typing import Any, List
from app.core.model.knowledge import KnowledgeChunk


class KnowledgeStore(ABC):
    """Knowledge store for storing docs, vectors, graphs."""

    @abstractmethod
    def __init__(self, name):
        """Init knowledge store."""

    @abstractmethod
    def load_document(self, file_path) -> str:
        """Load document."""

    @abstractmethod
    def delete_document(self, chunk_ids) -> None:
        """Delete document."""

    @abstractmethod
    def update_document(self, file_path, chunk_ids) -> str:
        """Update document."""

    @abstractmethod
    def retrieve(self, query) -> KnowledgeChunk:
        """retrieve knowledge from knowledge store."""

    @abstractmethod
    def clear(self) -> None:
        """clear all knowledge in knowledge store."""

    @abstractmethod
    def drop(self) -> None:
        """drop the entire knowledge store persistance data."""
