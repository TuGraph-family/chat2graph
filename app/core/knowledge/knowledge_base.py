from abc import ABC, abstractmethod
from typing import Any, List

class KnowledgeBase(ABC):
    """Knowledge base for storing docs, vectors, graphs."""

    @abstractmethod
    def __init__(self, name):
        """Init knowledge base."""

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
    def retrieve(self, query):
        """retrieve knowledge from knowledge base."""
    
    @abstractmethod
    def clear(self):
        """clear all knowledge in knowledge base."""
    
    @abstractmethod
    def delete(self):
        """delete the entire knowledge base persistance data."""
