from typing import Any, Dict, Tuple

from app.core.common.type import KnowledgeStoreType
from app.core.knowledge.knowledge_config import KnowledgeConfig
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.service.session_service import SessionService
from app.server.manager.view.knowledge_base_view import KnowledgeBaseViewTransformer


class KnowledgeBaseManager:
    """Knowledge Base Manager class to handle business logic"""

    def __init__(self):
        self._knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService.instance
        self._session_service: SessionService = SessionService.instance
        self._knowledge_base_view: KnowledgeBaseViewTransformer = KnowledgeBaseViewTransformer()

    def create_knowledge_base(
        self, name: str, knowledge_type: str, session_id: str
    ) -> Tuple[Dict[str, Any], str]:
        """Create a new knowledge base and return the response data.

        Args:
            name (str): Name of the knowledge base
            knowledge_type (str): Type of the knowledge base
            session_id (str): ID of the associated session

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing knowledge base details and success
                message
        """
        _ = self._session_service.get_session(session_id=session_id)

        knowledge_base = self._knowledge_base_service.create_knowledge_base(
            name=name, knowledge_type=KnowledgeStoreType(knowledge_type), session_id=session_id
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
            Tuple[Dict[str, Any], str]: A tuple containing knowledge base details and success
                message
        """
        knowledge_base = self._knowledge_base_service.get_knowledge_base(id=id)
        data = self._knowledge_base_view.serialize_knowledge_base(knowledge_base)
        return data, "Knowledge base fetched successfully"

    def update_knowledge_base(
        self, id: str, name: str, description: str
    ) -> Tuple[Dict[str, Any], str]:
        """Update a knowledge base by ID.

        Args:
            kb_id (str): ID of the knowledge base
            name (str): new name of the knowledge base
            description (str): new description of the knowledge base

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing edit status and success message
        """
        self._knowledge_base_service.update_knowledge_base(
            id=id, name=name, description=description
        )
        return {}, f"Knowledge base with ID {id} edited successfully"

    def delete_knowledge_base(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Delete a knowledge base by ID.

        Args:
            id (str): ID of the knowledge base

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        self._knowledge_base_service.delete_knowledge_base(id=id)
        return {}, f"Knowledge base with ID {id} deleted successfully"

    def get_all_knowledge_bases(self) -> Tuple[dict, str]:
        """
        Get all knowledge bases.

        Returns:
            Tuple[List[dict], str]: A tuple containing a list of knowledge base details and success
                message
        """
        global_knowledge_base, local_knowledge_bases = (
            self._knowledge_base_service.get_all_knowledge_bases()
        )
        data = self._knowledge_base_view.serialize_knowledge_bases(
            global_knowledge_base, local_knowledge_bases
        )

        return data, "Get all knowledge bases successfully"

    def load_knowledge(
        self, kb_id: str, file_id: str, knowledge_config: KnowledgeConfig
    ) -> Tuple[Dict[str, Any], str]:
        """Load knowledge with file ID.

        Args:
            kb_id (str): ID of the knowledge base
            file_id (str): ID of the file
            config (KnowledgeConfig): config for knowledge base file loading

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing load status and success message
        """
        self._knowledge_base_service.load_knowledge(
            knowledge_base_id=kb_id, file_id=file_id, knowledge_config=knowledge_config
        )
        return (
            {},
            f"File with ID {file_id} loaded into knowledge base with ID {kb_id} successfully",
        )

    def delete_knowledge(self, kb_id: str, file_id: str) -> Tuple[Dict[str, Any], str]:
        """Delete knowledge with file ID.

        Args:
            kb_id (str): ID of the knowledge base
            file_id (str): ID of the file

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing delete status and success message
        """
        self._knowledge_base_service.delete_knowledge(file_id=file_id)
        return (
            {},
            f"File with ID {file_id} deleted from knowledge base with ID {kb_id} successfully",
        )
