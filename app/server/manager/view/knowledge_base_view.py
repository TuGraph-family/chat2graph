from typing import Any, Dict, List

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
            "files": knowledge_base.file_descriptor_list,
        }

    @staticmethod
    def serialize_messages(global_knowledge_base: KnowledgeBase, local_knowledge_bases: List[KnowledgeBase]) -> List[Dict[str, Any]]:
        """Serialize a list of knowledge base to a list of API response dictionaries"""
        return {
            "global_knowledge_base": {"file_count": len(global_knowledge_base.file_descriptor_list)},
            "local_knowledge_base": [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "knowledge_type": kb.knowledge_type,
                    "session_id": kb.session_id,
                    "file_count": len(kb.file_descriptor_list),
                    "description": kb.description,
                    "time_stamp": kb.timestamp,
                }
                for kb in local_knowledge_bases
            ],
        }