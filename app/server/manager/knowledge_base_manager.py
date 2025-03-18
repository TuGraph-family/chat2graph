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
<<<<<<< HEAD
        self._knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService.instance
        self._session_service: SessionService = SessionService.instance
=======
        self._knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService()
        self._session_service: KnowledgeBaseService = SessionService()
>>>>>>> b9d0ea9 (load and delete knowledge)

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
        try:
            knowledge_bases = self._knowledge_base_service.get_all_knowledge_bases()
            knowledge_base_list = [
                {
                    "id": kb.id,
                    "name": kb.name,
                    "knowledge_type": kb.knowledge_type,
                    "session_id": kb.session_id,
                    "file_count": len(kb.files),
                    "description": kb.description
                }
                for kb in knowledge_bases
            ]
            return knowledge_base_list, "Get all knowledge bases successfully"
        except Exception as e:
            raise ServiceException(f"Failed to fetch all knowledge bases: {str(e)}") from e
    
    def load_knowledge(self, kb_id: str, file_id: str, config: str) -> Tuple[Dict[str, Any], str]:
        """Load knowledge with file ID.

        Args:
            kb_id (str): ID of the knowledge base
            file_id (str): ID of the file
            config (str): config for knowledge base file loading

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing load status and success message
        """
        try:
            self._knowledge_base_service.load_knowledge(knowledge_base_id=kb_id, file_id=file_id, config=config)
            return {}, f"File with ID {file_id} loaded into knowledge base with ID {kb_id} successfully"
        except Exception as e:
            raise ServiceException(f"Failed to load knowledge: {str(e)}") from e

    def delete_knowledge(self, kb_id: str, file_id: str) -> Tuple[Dict[str, Any], str]:
        """Delete knowledge with file ID.

        Args:
            kb_id (str): ID of the knowledge base
            file_id (str): ID of the file

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing delete status and success message
        """
        try:
            self._knowledge_base_service.delete_knowledge(file_id=file_id)
            return {}, f"File with ID {file_id} deleted from knowledge base with ID {kb_id} successfully"
        except Exception as e:
            raise ServiceException(f"Failed to delete knowledge: {str(e)}") from e
