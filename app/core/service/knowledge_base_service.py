import time
from typing import Any, Dict, List
import os
import json

from app.core.common.singleton import Singleton
from app.core.dal.dao.knowledge_dao import KnowledgeBaseDao, FileKbMappingDao
from app.core.dal.dao.file_dao import FileDao
from app.core.model.knowledge_base import KnowledgeBase
from app.core.model.knowledge import Knowledge
from app.core.knowledge.knowledge_store import KnowledgeStore
from app.core.knowledge.knowledge_store_factory import KnowledgeStoreFactory
from app.plugin.dbgpt.dbgpt_knowledge_store import VectorKnowledgeStore
from dbgpt.core import Chunk
from app.core.common.system_env import SystemEnv
from app.core.service.file_service import FileService
from sqlalchemy import func

GLOBAL_KB_ID = "global"


class KnowledgeBaseService(metaclass=Singleton):
    """Knowledge Base Service"""

    def __init__(self):
        self._knowledge_base_dao: KnowledgeBaseDao = KnowledgeBaseDao.instance
        self._file_dao: FileDao = FileDao.instance
        self._file_kb_mapping_dao: FileKbMappingDao = FileKbMappingDao.instance
        # create global knowledge store
        self._global_knowledge_store: KnowledgeStore = KnowledgeStoreFactory.get_or_create("global_knowledge_store")

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
        return KnowledgeBase(
            id=result.id,
            name=result.name,
            knowledge_type=result.knowledge_type,
            session_id=result.session_id,
            file_descriptor_list=[],
            description="",
            timestamp=result.timestamp,
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
        # fetch all related file_kb_mapping
        mappings = self._file_kb_mapping_dao.filter_by(kb_id=result.id)
        file_descriptor_list = [
            {
                "name": mapping.name,
                "type": mapping.type,
                "size": mapping.size,
                "status": mapping.status,
                "time_stamp": mapping.timestamp,
                "file_id": mapping.id,
            }
            for mapping in mappings
        ]
        if not result:
            raise ValueError(f"Knowledge base with ID {id} not found")
        return KnowledgeBase(
            id=result.id,
            name=result.name,
            knowledge_type=result.knowledge_type,
            session_id=result.session_id,
            file_descriptor_list=file_descriptor_list,
            description=result.description,
            timestamp=result.timestamp,
        )

    def edit_knowledge_base(self, id: str, name: str, description: str):
        """edit a knowledge base by ID.
        Args:
            id (str): ID of the knowledge base
        """
        # delete the knowledge base
        knowledge_base = self._knowledge_base_dao.get_by_id(id=id)
        if not knowledge_base:
            raise ValueError(f"Knowledge base with ID {id} not found")
        self._knowledge_base_dao.update(
            id=id, name=name, description=description, timestamp=func.strftime("%s", "now")
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
        # delte all related file and file_kb_mapping from db
        mappings = self._file_kb_mapping_dao.filter_by(kb_id=id)
        for mapping in mappings:
            self._file_kb_mapping_dao.delete(id=mapping.id)
            FileService.instance.delete_file(id=mapping.id)
        # delete kb from db
        self._knowledge_base_dao.delete(id=id)
        # delete knolwledge base folder
        KnowledgeStoreFactory.get_or_create(id).drop()

    def get_all_knowledge_bases(self) -> tuple[KnowledgeBase, List[KnowledgeBase]]:
        """Get all knowledge bases.
        Returns:
            List[KnowledgeBase]: List of knowledge bases
        """

        # get local knowledge bases
        results = self._knowledge_base_dao.get_all()
        # get global knowledge base
        mappings = self._file_kb_mapping_dao.filter_by(kb_id=GLOBAL_KB_ID)
        global_file_descriptor_list = [
            {
                "name": mapping.name,
                "type": mapping.type,
                "size": mapping.size,
                "status": mapping.status,
                "time_stamp": mapping.timestamp,
                "file_id": mapping.id,
            }
            for mapping in mappings
        ]
        global_kb = KnowledgeBase(
            id=GLOBAL_KB_ID,
            name="global_knowledge_store",
            knowledge_type="",
            session_id="",
            file_descriptor_list=global_file_descriptor_list,
            description="",
            timestamp=0,
        )
        # get local knowledge bases
        local_kbs = []
        for result in results:
            mappings = self._file_kb_mapping_dao.filter_by(kb_id=result.id)
            file_descriptor_list = [
                {
                    "name": mapping.name,
                    "type": mapping.type,
                    "size": mapping.size,
                    "status": mapping.status,
                    "time_stamp": mapping.timestamp,
                    "file_id": mapping.id,
                }
                for mapping in mappings
            ]
            local_kbs.append(
                KnowledgeBase(
                    id=result.id,
                    name=result.name,
                    knowledge_type=result.knowledge_type,
                    session_id=result.session_id,
                    file_descriptor_list=file_descriptor_list,
                    description=result.description,
                    timestamp=result.timestamp,
                )
            )
        return global_kb, local_kbs

    def get_knowledge(self, query, job) -> Any:
        """Get knowledge by ID."""
        # get global knowledge
        global_chunks = self._global_knowledge_store.retrieve(query)
        # get local knowledge
        kbs = self._knowledge_base_dao.filter_by(session_id=job.session_id)
        if len(kbs) == 1:
            kb = kbs[0]
            knowledge_base_id = kb.id
            local_chunks = KnowledgeStoreFactory.get_or_create(knowledge_base_id).retrieve(query)
        else:
            local_chunks = []
        return Knowledge(global_chunks, local_chunks)

    def load_knowledge(self, knowledge_base_id, file_id, config):
        """Load new knowledge entry."""
        # get file with file id
        file = self._file_dao.get_by_id(id=file_id)
        folder_path = file.path
        file_name = file.name
        file_path = os.path.join(folder_path, os.listdir(folder_path)[0])
        # add file_kb_mapping
        if self._file_kb_mapping_dao.get_by_id(id=file_id) == None:
            self._file_kb_mapping_dao.create(
                id=file_id,
                name=file_name,
                kb_id=knowledge_base_id,
                status="pending",
                config=config,
                size=os.path.getsize(file_path),
                type="local",
            )
        # update knowledge base timestamp
        if knowledge_base_id != GLOBAL_KB_ID:
            timestamp = self._file_kb_mapping_dao.get_by_id(id=file_id).timestamp
            self._knowledge_base_dao.update(id=knowledge_base_id, timestamp=timestamp)
        # load config
        config = json.loads(config)
        # load file to knowledge base
        try:
            if knowledge_base_id != GLOBAL_KB_ID:
                chunk_ids = KnowledgeStoreFactory.get_or_create(knowledge_base_id).load_document(file_path, config)
            else:
                chunk_ids = self._global_knowledge_store.load_document(file_path, config)
        except Exception as e:
            self._file_kb_mapping_dao.update(id=file_id, status="fail")
            raise e
        else:
            self._file_kb_mapping_dao.update(id=file_id, status="success", chunk_ids=chunk_ids)

    def delete_knowledge(self, file_id):
        """Delete knowledge entry."""
        # get chunk_ids and kb_id with file_id
        file_kb_mapping = self._file_kb_mapping_dao.get_by_id(id=file_id)
        chunk_ids = file_kb_mapping.chunk_ids
        knowledge_base_id = file_kb_mapping.kb_id
        # delete related chunks from knowledge base
        if knowledge_base_id != GLOBAL_KB_ID:
            KnowledgeStoreFactory.get_or_create(knowledge_base_id).delete_document(chunk_ids)
        else:
            self._global_knowledge_store.delete_document(chunk_ids)
        # delete related file_kb_mapping
        self._file_kb_mapping_dao.delete(id=file_id)
        # delete related virtual file
        FileService.instance.delete_file(id=file_id)
        # update knowledge base timestamp
        if knowledge_base_id != GLOBAL_KB_ID:
            self._knowledge_base_dao.update(id=knowledge_base_id, timestamp=func.strftime("%s", "now"))

    def __delete__(self):
        self._global_knowledge_base.clear()
