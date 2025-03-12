from enum import Enum
from typing import Any, Dict, List, Tuple

from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.service.session_service import SessionService


# TODO: move to the common module
class KnowledgeBaseType(Enum):
    """Knowledge base type Enum"""

    PUBLIC = "public"
    PRIVATE = "private"


class KnowledgeBaseManager:
    """Knowledge Base Manager class to handle business logic"""

    def __init__(self):
        self._knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService.instance
        self._session_service: SessionService = SessionService.instance

    def create_knowledge_base(
        self, name: str, knowledge_type: str, session_id: str
    ) -> Tuple[Dict[str, Any], str]:
        """Create a new knowledge base and return the response data.

        Args:
            name (str): Name of the knowledge base
            knowledge_type (str): Type of the knowledge base
            session_id (str): ID of the associated session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing knowledge base details and success message
        """
        _ = self._session_service.get_session(session_id=session_id)

        knowledge_base = self._knowledge_base_service.create_knowledge_base(
            name=name, knowledge_type=knowledge_type, session_id=session_id
        )
        # TODO: use knowledge base type Enum
        data = {
            "id": knowledge_base.id,
            "name": knowledge_base.name,
            "knowledge_type": knowledge_base.knowledge_type,
            "session_id": knowledge_base.session_id,
        }
        return data, "Knowledge base created successfully"

    def get_knowledge_base(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Get knowledge base details by ID.

        Args:
            id (str): ID of the knowledge base

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing knowledge base details and success message
        """
        knowledge_base = self._knowledge_base_service.get_knowledge_base(id=id)
        data = {
            "id": knowledge_base.id,
            "name": knowledge_base.name,
            "knowledge_type": knowledge_base.knowledge_type,
            "session_id": knowledge_base.session_id,
        }
        return data, "Knowledge base fetched successfully"

    def delete_knowledge_base(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Delete a knowledge base by ID.

        Args:
            id (str): ID of the knowledge base

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        self._knowledge_base_service.delete_knowledge_base(id=id)
        return {}, f"Knowledge base with ID {id} deleted successfully"

    def get_all_knowledge_bases(self) -> Tuple[List[dict], str]:
        """
        Get all knowledge bases.

        Returns:
            Tuple[List[dict], str]: A tuple containing a list of knowledge base details and success
                message
        """
        knowledge_bases = self._knowledge_base_service.get_all_knowledge_bases()
        knowledge_base_list = [
            {
                "id": kb.id,
                "name": kb.name,
                "knowledge_type": kb.knowledge_type,
                "session_id": kb.session_id,
            }
            for kb in knowledge_bases
        ]
        return knowledge_base_list, "Get all knowledge bases successfully"
