import time
from typing import Any, Dict, List
import os

from app.core.common.singleton import Singleton
from app.core.dal.dao import KnowledgeBaseDAO
from app.core.dal.database import DB
from app.core.model.knowledge_base import KnowledgeBase
from app.core.knowledge.knowledge import Knowledge
from app.server.common.util import ServiceException
from app.plugin.dbgpt.dbgpt_knowledge_base import VectorKnowledgeBase
from dbgpt.core import Chunk
from app.core.common.async_func import run_async_function

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GLOBAL_KNOWLEDGE_PATH = ROOT_PATH + "/app/core/knowledge/global_knowledge"

class KnowledgeBaseService(metaclass=Singleton):
    """Knowledge Base Service"""

    def __init__(self):
        self._global_knowledge_base = VectorKnowledgeBase("global_knowledge_base")
        for root, dirs, files in os.walk(GLOBAL_KNOWLEDGE_PATH):
            for file in files:
                run_async_function(self._global_knowledge_base.load_document, root+"/"+file)
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
        result = self._knowledge_base_dao.create(
            name=name, knowledge_type=knowledge_type, session_id=session_id
        )
        return Knowledge(
            id=str(result.id),
            name=str(result.name),
            knowledge_type=str(result.knowledge_type),
            session_id=str(result.session_id),
        )

    def get_knowledge_base(self, id: str) -> Knowledge:
        """Get a knowledge base by ID.

        Args:
            id (str): ID of the knowledge base
        Returns:
            KnowledgeBase: Knowledge base object
        """
        # fetch the knowledge base
        result = self._knowledge_base_dao.get_by_id(id=id)
        if not result:
            raise ValueError(f"Knowledge base with ID {id} not found")
        return Knowledge(
            id=str(result.id),
            name=str(result.name),
            knowledge_type=str(result.knowledge_type),
            session_id=str(result.session_id),
        )

    def delete_knowledge_base(self, id: str):
        """Delete a knowledge base by ID.
        Args:
            id (str): ID of the knowledge base
        """
        # delete the knowledge base
        knowledge_base = self._knowledge_base_dao.get_by_id(id=id)
        if not knowledge_base:
            raise ValueError(f"Knowledge base with ID {id} not found")
        self._knowledge_base_dao.delete(id=id)

    def update_knowledge_base(self) -> Knowledge:
        """Update a knowledge base by ID."""
        raise NotImplementedError("Method not implemented")

    def get_all_knowledge_bases(self) -> List[Knowledge]:
        """Get all knowledge bases.
        Returns:
            List[KnowledgeBase]: List of knowledge bases
        """

        results = self._knowledge_base_dao.get_all()
        return [
            Knowledge(
                id=str(result.id),
                name=str(result.name),
                knowledge_type=str(result.knowledge_type),
                session_id=str(result.session_id),
            )
            for result in results
        ]
    
    async def get_knowledge(self, query, session_id) -> Any:
        """Get knowledge by ID."""
        global_chunks = await self._global_knowledge_base.retrieve(query)
        # local_chunk = await VectorKnowledgeBase(knowledge_base_id).retrieve(query)
        local_chunks = [Chunk(content="")]
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return Knowledge(global_chunks, local_chunks, timestamp)
    
    async def load_knowledge(self, knowledge_base_id, file_path):
        """Load new knowledge entry."""
        await VectorKnowledgeBase(knowledge_base_id).load_document(file_path)

    def delete_knowledge(self, knowledge_base_id, file_name):
        """Delete knowledge entry."""
        VectorKnowledgeBase(knowledge_base_id).delete_document(chunk_ids)
    
    def __delete__(self):
        self._global_knowledge_base.clear()
