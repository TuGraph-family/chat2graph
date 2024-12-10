from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class KnowledgeBaseType(Enum):
    """Knowledge base type"""

    # TODO: The names of these types are under discussions
    GRAPH_DB = "graph_db"
    VECTOR_DB = "vector_db"


class KnowledgeBaseProvider(ABC):
    """SPI Interface for knowledge base providers.
    Implementations should be registered via entry points.
    """

    @abstractmethod
    def query(self, query: Any) -> Any:
        """Execute a knowledge query"""

    @abstractmethod
    def get_knowledge(self, *args, **kwargs) -> Any:
        """Get knowledge by ID"""


class KnowledgeBaseRegistry:
    """Registry for knowledge base providers"""

    # TODO: Disccuss: Do we need @classmethod here?
    @classmethod
    def discover_providers(cls) -> Dict[KnowledgeBaseType, type[KnowledgeBaseProvider]]:
        """Discover knowledge base providers"""
        # TODO: Implement the more sophisticated discovery mechanism
        return {
            KnowledgeBaseType.GRAPH_DB: BuiltinKnowledgeBaseProvider,
            KnowledgeBaseType.VECTOR_DB: BuiltinKnowledgeBaseProvider,
        }


class BuiltinKnowledgeBaseProvider(KnowledgeBaseProvider):
    """Builtin knowledge base provider"""

    def query(self, query: Any) -> Any:
        """Execute a knowledge query"""
        # TODO: Implement the query retrieval

    def get_knowledge(self, *args, **kwargs) -> Any:
        """Get knowledge by ID"""
        # TODO: Implement the knowledge retrieval


class KnowledgeBaseFactory:
    """Factory for knowledge base providers"""

    def __init__(self):
        self._providers = KnowledgeBaseRegistry.discover_providers()
        self._instances: Dict[str, KnowledgeBaseProvider] = {}

    def get_provider(
        self, provider_id: str, provider_typ: Optional[KnowledgeBaseType]
    ) -> KnowledgeBaseProvider:
        """Get a knowledge base provider by ID"""
        if provider_id not in self._instances:
            if provider_typ is None:
                raise ValueError(f"Provider type is required: {provider_id}")
            if provider_typ not in self._providers:
                raise ValueError(f"Unknown provider: {provider_id}, {provider_typ}")
            self._instances[provider_id] = self._providers[provider_typ]()
        return self._instances[provider_id]
