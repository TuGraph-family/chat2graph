from typing import Dict, List

from app.core.common.singleton import Singleton
from app.core.dal.dao import KnowledgeBaseDAO
from app.core.dal.database import DB
from app.core.model.knowledge_base import KnowledgeBase
from app.server.common.util import ServiceException


class KnowledgeBaseService(metaclass=Singleton):
    """Knowledge Base Service"""

    def __init__(self):
        self._knowledge_bases: Dict[str, KnowledgeBase] = {}
        self._dao: KnowledgeBaseDAO = KnowledgeBaseDAO(DB())

    def create_knowledge_base(
        self, name: str, knowledge_type: str, session_id: str
    ) -> KnowledgeBase:
        """Create a new knowledge base.

        Args:
            name (str): Name of the knowledge base
            knowledge_type (str): Type of the knowledge base
            session_id (str): ID of the session

        Returns:
            KnowledgeBase: Knowledge base object
        """
        # create the knowledge base
        result = self._dao.create(name=name, knowledge_type=knowledge_type, session_id=session_id)
        return KnowledgeBase(
            id=result.id,
            name=result.name,
            knowledge_type=result.knowledge_type,
            session_id=result.session_id,
        )

    def get_knowledge_base(self, id: str) -> KnowledgeBase:
        """Get a knowledge base by ID.

        Args:
            id (str): ID of the knowledge base
        Returns:
            KnowledgeBase: Knowledge base object
        """
        # fetch the knowledge base
        result = self._dao.get_by_id(id=id)
        if not result:
            raise ServiceException(f"Knowledge base with ID {id} not found")
        return KnowledgeBase(
            id=result.id,
            name=result.name,
            knowledge_type=result.knowledge_type,
            session_id=result.session_id,
        )

    def delete_knowledge_base(self, id: str):
        """Delete a knowledge base by ID.
        Args:
            id (str): ID of the knowledge base
        """
        # delete the knowledge base
        knowledge_base = self._dao.get_by_id(id=id)
        if not knowledge_base:
            raise ServiceException(f"Knowledge base with ID {id} not found")
        self._dao.delete(id=id)

    def update_knowledge_base(self) -> KnowledgeBase:
        """Update a knowledge base by ID."""

    def get_all_knowledge_bases(self) -> List[KnowledgeBase]:
        """Get all knowledge bases.
        Returns:
            List[KnowledgeBase]: List of knowledge bases
        """

        results = self._dao.get_all()
        return [
            KnowledgeBase(
                id=result.id,
                name=result.name,
                knowledge_type=result.knowledge_type,
                session_id=result.session_id,
            )
            for result in results
        ]
