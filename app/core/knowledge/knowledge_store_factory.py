from app.core.common.system_env import SystemEnv
from app.core.common.type import KnowledgeStoreType
from app.core.knowledge.knowledge_store import KnowledgeStore
from app.plugin.dbgpt.dbgpt_knowledge_store import VectorKnowledgeStore, GraphKnowledgeStore


class KnowledgeStoreFactory:
    """Knowledge store factory."""

    @classmethod
    def get_or_create(cls, name: str) -> KnowledgeStore:
        """Get ore create a knowledge store."""
        if SystemEnv.KNOWLEDGE_STORE_TYPE == KnowledgeStoreType.VECTOR:
            return VectorKnowledgeStore(name)
        elif SystemEnv.KNOWLEDGE_STORE_TYPE == KnowledgeStoreType.GRAPH:
            return GraphKnowledgeStore(name)

        raise ValueError(f"Cannot create knowledge store of type {SystemEnv.NOWLEDGE_STORE_TYPE}")
