from typing import Any, Dict, List

from app.core.knowledge.knowledge_config import KnowledgeConfig
from app.core.model.knowledge_base import KnowledgeBase


class KnowledgeBaseViewTransformer:
    """Knowledge base view transformer responsible for transforming internal knowledge base models to API response
        formats.

    This class ensures that internal field names (like timestamp) are
    properly converted to API field names (like time_stamp) for consistent API responses.
    """

    @staticmethod
    def serialize_knowledge_base(knowledge_base: KnowledgeBase) -> Dict[str, Any]:
        """Convert a KnowledgeBase model to an API response dictionary."""
        return {
            "id": knowledge_base.id,
            "name": knowledge_base.name,
            "knowledge_type": knowledge_base.knowledge_type,
            "session_id": knowledge_base.session_id,
            "time_stamp": knowledge_base.timestamp,
            "files": [
                {
                    "name": file_descriptor.name,
                    "type": file_descriptor.type.value,
                    "size": file_descriptor.size,
                    "status": file_descriptor.status.value,
                    "time_stamp": file_descriptor.timestamp,
                    "file_id": file_descriptor.id,
                }
                for file_descriptor in knowledge_base.file_descriptors
            ],
            "description": knowledge_base.description,
        }

    @staticmethod
    def serialize_knowledge_bases(
        global_knowledge_base: KnowledgeBase,
        local_knowledge_bases: List[KnowledgeBase],
    ) -> Dict[str, Any]:
        """Serialize a list of knowledge base to a list of API response dictionaries"""
        return {
            "global_knowledge_base": {
                "id": global_knowledge_base.id,
                "name": global_knowledge_base.name,
                "knowledge_type": global_knowledge_base.knowledge_type,
                "session_id": global_knowledge_base.session_id,
                "file_count": len(global_knowledge_base.file_descriptors),
                "description": global_knowledge_base.description,
                "time_stamp": global_knowledge_base.timestamp,
            },
            "local_knowledge_base": [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "knowledge_type": kb.knowledge_type,
                    "session_id": kb.session_id,
                    "file_count": len(kb.file_descriptors),
                    "description": kb.description,
                    "time_stamp": kb.timestamp,
                }
                for kb in local_knowledge_bases
            ],
        }

    @staticmethod
    def deserialize_knowledge_config(data: Dict[str, Any]) -> KnowledgeConfig:
        """Deserialize knowledge config data from API request."""
        knowledge_config = KnowledgeConfig()
        knowledge_config.chunk_size = data.get("chunk_size", knowledge_config.chunk_size)
        return knowledge_config
