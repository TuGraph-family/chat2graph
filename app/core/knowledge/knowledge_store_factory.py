from app.core.common.type import KnowledgeBaseType
from app.core.knowledge.knowledge_store import KnowledgeStore
from app.plugin.dbgpt.dbgpt_knowledge_store import VectorKnowledgeStore, GraphKnowledgeStore


class KnowledgeStoreFactory:
    """Knowledge store factory."""

    @classmethod
    def get_or_create(cls, knowledge_base_type: KnowledgeBaseType, name: str) -> KnowledgeStore:
        """Get ore create a knowledge store."""
        if knowledge_base_type == KnowledgeBaseType.VECTOR:
            return VectorKnowledgeStore(name)
        elif knowledge_base_type == KnowledgeBaseType.GRAPH:
            return GraphKnowledgeStore(name)

        raise ValueError(f"Cannot create model service of type {platform_type}")
