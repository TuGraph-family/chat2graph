from abc import ABC, abstractmethod
from typing import Any
from app.plugin.dbgpt.dbgpt_knowledge_base import VectorKnowledgeBase
import os


ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GLOBAL_KNOWLEDGE_PATH = ROOT_PATH + "/app/core/knowledge/global_knowledge"

class KnowledgeService:
    """Knowledge base service."""

    def __init__(self):
        self._global_knowledge_base = VectorKnowledgeBase("global_knowledge_base")

    async def get_knowledge(self, query, knowledge_base_id) -> Any:
        """Get knowledge by ID."""
        global_chunk = await self._global_konwledge_base.retrieve(query)
        local_chunk = await VectorKnowledgeBase(knowledge_base_id).retrieve(query)
        return global_chunk, local_chunk
    
    async def load_knowledge(self, knowledge_base_id, file_path):
        """Load new knowledge entry."""
        await VectorKnowledgeBase(knowledge_base_id).load_document(file_path)

    async def update_knowledge(self, knowledge_base_id, file_path, chunk_ids):
        """Update existing knowledge entry."""
        await VectorKnowledgeBase(knowledge_base_id).update_document(file_path, chunk_ids)

    def delete_knowledge(self, knowledge_base_id, chunk_ids):
        """Delete knowledge entry."""
        VectorKnowledgeBase(knowledge_base_id).delete_document(chunk_ids)
    
    def __delete__(self):
        self._global_knowledge_base.clear()
