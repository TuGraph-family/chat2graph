import time
from typing import Any, Dict, List
import os
import json

from app.core.common.singleton import Singleton
from app.core.dal.dao import KnowledgeBaseDAO, FileDAO, FileToKBDAO
from app.core.dal.database import DB
from app.core.model.knowledge_base import KnowledgeBase
from app.core.knowledge.knowledge import Knowledge
from app.server.common.util import ServiceException
from app.plugin.dbgpt.dbgpt_knowledge_base import VectorKnowledgeBase
from dbgpt.core import Chunk
from app.core.common.async_func import run_async_function
from app.core.common.system_env import SystemEnv

class KnowledgeBaseService(metaclass=Singleton):
    """Knowledge Base Service"""

    def __init__(self):
        self._global_knowledge_base = VectorKnowledgeBase("global_knowledge_base")
        for root, dirs, files in os.walk(SystemEnv.APP_ROOT+"/global_knowledge"):
            for file in files:
                self._global_knowledge_base.load_document(root+"/"+file)
        self._knowledge_base_dao: KnowledgeBaseDAO = KnowledgeBaseDAO(DB())
        self._file_dao: FileDAO = FileDAO(DB())
        self._file_to_kb_dao: FileToKBDAO = FileToKBDAO(DB())

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
        result = self._knowledge_base_dao.create(name=name, knowledge_type=knowledge_type, session_id=session_id)
        return KnowledgeBase(
            id=result.id,
            name=result.name,
            knowledge_type=result.knowledge_type,
            session_id=result.session_id,
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
        # get global knowledge
        global_chunks = await self._global_knowledge_base.retrieve(query)
        # get local knowledge
        kbs = self._knowledge_base_dao.filter_by(session_id=session_id)
        if len(kbs) == 1:
            knowledge_base_id = kbs[0].id
            local_chunks = await VectorKnowledgeBase(knowledge_base_id).retrieve(query)
        else:
            local_chunks = [Chunk(content="")]
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ")
        return Knowledge(global_chunks, local_chunks, timestamp)
    
    def load_knowledge(self, knowledge_base_id, file_id, config):
        """Load new knowledge entry."""
        # get file with file id
        file = self._file_dao.get_by_id(id=file_id)
        folder_path = file.path
        file_name = file.name
        file_path = os.path.join(folder_path, os.listdir(folder_path)[0])
        # add file_to_kb
        if self._file_to_kb_dao.get_by_id(id=file_id) == None:
            self._file_to_kb_dao.create(id=file_id, name=file_name, kb_id=knowledge_base_id, status="pending", config=config)
        # load file to knowledge base
        try:
            config = json.loads(config)
            chunk_ids = VectorKnowledgeBase(knowledge_base_id).load_document(file_path, config)
        except Exception as e:
            self._file_to_kb_dao.update(id=file_id, status="fail")
        else:
            self._file_to_kb_dao.update(id=file_id, status="success", chunk_ids=chunk_ids)

    def delete_knowledge(self, file_id):
        """Delete knowledge entry."""
        # get file with file id
        file = self._file_dao.get_by_id(id=file_id)
        path = file.path
        # get chunk_ids and kb_id with file_id
        file_to_kb = self._file_to_kb_dao.get_by_id(id=file_id)
        chunk_ids = file_to_kb.chunk_ids
        knowledge_base_id = file_to_kb.kb_id
        # delete related chunks from knowledge base
        VectorKnowledgeBase(knowledge_base_id).delete_document(chunk_ids)
        # delete virtual file from db
        self._file_dao.delete(id=file_id)
        # delete physical file if all references are deleted
        results = self._file_dao.filter_by(path=path)
        if len(results)==0:
            for file_name in os.listdir(path):
                file_path = os.path.join(path, file_name)
                os.remove(file_path)
        os.rmdir(path)
    
    def __delete__(self):
        self._global_knowledge_base.clear()
