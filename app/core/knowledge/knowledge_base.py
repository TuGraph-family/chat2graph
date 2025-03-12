from abc import ABC, abstractmethod
from typing import Any, List

class KnowledgeBase(ABC):
    """Knowledge base for storing docs, vectors, graphs."""

    @abstractmethod
    def __init__(self, name):
        """Init knowledge base."""

    @abstractmethod
    async def load_document(self, file_path) -> List[str]:
        """Load document."""

    @abstractmethod
    def delete_document(self, chunk_ids):
        """Delete document."""

    @abstractmethod
    async def update_document(self, file_path, chunk_ids) -> List[str]:
        """Update document."""
    
    @abstractmethod
    async def retrieve(self, query):
        """retrieve knowledge from knowledge base."""
    
    @abstractmethod
    async def clear(self):
        """clear all knowledge in knowledge base."""
