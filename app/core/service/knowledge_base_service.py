import json
import os
from typing import List, Optional, Tuple

from sqlalchemy import func

from app.core.common.singleton import Singleton
from app.core.common.system_env import SystemEnv
from app.core.common.type import (
    FileStorageType,
    KnowledgeStoreCategory,
    KnowledgeStoreFileStatus,
    KnowledgeStoreType,
)
from app.core.dal.dao.file_descriptor_dao import FileDescriptorDao
from app.core.dal.dao.knowledge_dao import FileKbMappingDao, KnowledgeBaseDao
from app.core.knowledge.knowledge_config import KnowledgeConfig
from app.core.knowledge.knowledge_store_factory import KnowledgeStoreFactory
from app.core.model.file_descriptor import FileDescriptor
from app.core.model.knowledge import Knowledge
from app.core.model.knowledge_base import (
    GlobalKnowledgeBase,
    KnowledgeBase,
)
from app.core.service.file_service import FileService


class KnowledgeBaseService(metaclass=Singleton):
    """Knowledge Base Service"""

    def __init__(self):
        self._knowledge_base_dao: KnowledgeBaseDao = KnowledgeBaseDao.instance
        self._file_descriptor_dao: FileDescriptorDao = FileDescriptorDao.instance
        self._file_kb_mapping_dao: FileKbMappingDao = FileKbMappingDao.instance
        # create global knowledge store
        if (
            len(self._knowledge_base_dao.filter_by(category=KnowledgeStoreCategory.GLOBAL.value))
            == 0
        ):
            self._knowledge_base_dao.create(
                name=SystemEnv.GLOBAL_KNOWLEDGE_BASE_NAME,
                knowledge_type=SystemEnv.KNOWLEDGE_STORE_TYPE.value,
                session_id="",
                category=KnowledgeStoreCategory.GLOBAL.value,
            )
        self._global_kb_do = self._knowledge_base_dao.filter_by(
            category=KnowledgeStoreCategory.GLOBAL.value
        )[0]

    def create_knowledge_base(
        self, name: str, knowledge_type: KnowledgeStoreType, session_id: str
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
            name=name,
            knowledge_type=knowledge_type.value,
            session_id=session_id,
            category=KnowledgeStoreCategory.LOCAL.value,
        )
        return KnowledgeBase(
            id=str(result.id),
            name=str(result.name),
            knowledge_type=str(result.knowledge_type),
            session_id=str(result.session_id),
            file_descriptors=[],
            description="",
            category=str(result.category),
            timestamp=int(result.timestamp),
        )

    def get_knowledge_base(self, id: str) -> KnowledgeBase:
        """Get a knowledge base by ID.

        Args:
            id (str): ID of the knowledge base
        Returns:
            KnowledgeBase: Knowledge base object
        """
        # fetch the knowledge base
        result = self._knowledge_base_dao.get_by_id(id=id)
        if result:
            # fetch all related file_kb_mapping
            mappings = self._file_kb_mapping_dao.filter_by(kb_id=result.id)
            file_descriptors = [
                FileDescriptor(
                    id=str(mapping.id),
                    path=None,
                    name=str(mapping.name),
                    type=FileStorageType(mapping.type),
                    size=str(mapping.size),
                    status=KnowledgeStoreFileStatus(mapping.status),
                    timestamp=int(mapping.timestamp),
                )
                for mapping in mappings
            ]
            return KnowledgeBase(
                id=str(result.id),
                name=str(result.name),
                knowledge_type=str(result.knowledge_type),
                session_id=str(result.session_id),
                file_descriptors=file_descriptors,
                description=str(result.description),
                category=str(result.category),
                timestamp=int(result.timestamp),
            )
        raise ValueError(f"Cannot find knowledge base with ID {id}")

    def get_session_knowledge_base(self, session_id: str) -> Optional[KnowledgeBase]:
        """Get a knowledge base by Session ID."""

        # fetch the knowledge base
        results = self._knowledge_base_dao.filter_by(session_id=session_id)
        result = results[0] if results else None

        if result:
            return KnowledgeBase(
                id=str(result.id),
                name=str(result.name),
                knowledge_type=str(result.knowledge_type),
                session_id=str(result.session_id),
                file_descriptors=[],
                description=str(result.description),
                category=str(result.category),
                timestamp=int(result.timestamp),
            )

        return None

    def update_knowledge_base(self, id: str, name: str, description: str) -> None:
        """Update a knowledge base by ID.
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

    def clean_knowledge_base(self, id: str, drop: bool) -> None:
        # delete all related file and file_kb_mapping from db
        mappings = self._file_kb_mapping_dao.filter_by(kb_id=id)
        for mapping in mappings:
            self._file_kb_mapping_dao.delete(id=str(mapping.id))
            FileService.instance.delete_file(id=str(mapping.id))
        if drop:
            # get the knowledge base from db
            knowledge_base = self._knowledge_base_dao.get_by_id(id=id)
            if not knowledge_base:
                raise ValueError(f"Knowledge base with ID {id} not found")
            # delete kb from db
            self._knowledge_base_dao.delete(id=id)
            # drop knowledge base folder
            KnowledgeStoreFactory.get_or_create(id).drop()

    def get_all_knowledge_bases(self) -> Tuple[KnowledgeBase, List[KnowledgeBase]]:
        """Get all knowledge bases.

        Returns:
            Tuple[KnowledgeBase, List[KnowledgeBase]]: A tuple containing global knowledge base and
                list of local knowledge
        """

        # get local knowledge bases
        results = self._knowledge_base_dao.filter_by(category=KnowledgeStoreCategory.LOCAL.value)
        # get global knowledge base
        mappings = self._file_kb_mapping_dao.filter_by(kb_id=self._global_kb_do.id)
        global_file_descriptors = [
            FileDescriptor(
                id=str(mapping.id),
                path=None,
                name=str(mapping.name),
                type=FileStorageType(mapping.type),
                size=str(mapping.size),
                status=KnowledgeStoreFileStatus(mapping.status),
                timestamp=int(mapping.timestamp),
            )
            for mapping in mappings
        ]
        global_kb = GlobalKnowledgeBase(
            id=str(self._global_kb_do.id),
            name=str(self._global_kb_do.name),
            knowledge_type=str(self._global_kb_do.knowledge_type),
            session_id=str(self._global_kb_do.session_id),
            file_descriptors=global_file_descriptors,
            description=str(self._global_kb_do.description),
            category=str(self._global_kb_do.category),
            timestamp=int(self._global_kb_do.timestamp),
        )
        # get local knowledge bases
        local_kbs = []
        for result in results:
            mappings = self._file_kb_mapping_dao.filter_by(kb_id=result.id)
            file_descriptors = [
                FileDescriptor(
                    id=str(mapping.id),
                    path=None,
                    name=str(mapping.name),
                    type=FileStorageType(mapping.type),
                    size=str(mapping.size),
                    status=KnowledgeStoreFileStatus(mapping.status),
                    timestamp=int(mapping.timestamp),
                )
                for mapping in mappings
            ]
            local_kbs.append(
                KnowledgeBase(
                    id=str(result.id),
                    name=str(result.name),
                    knowledge_type=str(result.knowledge_type),
                    session_id=str(result.session_id),
                    file_descriptors=file_descriptors,
                    description=str(result.description),
                    category=str(result.category),
                    timestamp=int(result.timestamp),
                )
            )
        return global_kb, local_kbs

    def get_knowledge(self, query: str, session_id: Optional[str]) -> Knowledge:
        """Get knowledge by ID."""
        # get global knowledge
        global_chunks = KnowledgeStoreFactory.get_or_create(str(self._global_kb_do.id)).retrieve(
            query
        )
        # get local knowledge
        local_chunks = []
        if session_id:
            kbs = self._knowledge_base_dao.filter_by(session_id=session_id)
            if len(kbs) == 1:
                kb = kbs[0]
                knowledge_base_id = kb.id
                local_chunks = KnowledgeStoreFactory.get_or_create(str(knowledge_base_id)).retrieve(
                    query
                )
        return Knowledge(global_chunks, local_chunks)

    def load_knowledge(
        self, knowledge_base_id: str, file_id: str, knowledge_config: KnowledgeConfig
    ) -> None:
        """Load new knowledge entry."""
        # get file with file id
        file_descriptor_do = self._file_descriptor_dao.get_by_id(id=file_id)
        if file_descriptor_do:
            folder_path = file_descriptor_do.path
            file_name = file_descriptor_do.name
            file_path = os.path.join(folder_path, os.listdir(folder_path)[0])

            # add file_kb_mapping
            if self._file_kb_mapping_dao.get_by_id(id=file_id) is None:
                self._file_kb_mapping_dao.create(
                    id=file_id,
                    name=file_name,
                    kb_id=knowledge_base_id,
                    status=KnowledgeStoreFileStatus.PENDING.value,
                    config=json.dumps(knowledge_config.to_dict()),
                    size=os.path.getsize(file_path),
                    type=FileStorageType.LOCAL.value,
                )

            # update knowledge base timestamp
            mapping = self._file_kb_mapping_dao.get_by_id(id=file_id)
            if mapping:
                timestamp = mapping.timestamp
                self._knowledge_base_dao.update(id=knowledge_base_id, timestamp=timestamp)
                if mapping.status != KnowledgeStoreFileStatus.SUCCESS.value:
                    # load file to knowledge base
                    try:
                        chunk_ids = KnowledgeStoreFactory.get_or_create(
                            knowledge_base_id
                        ).load_document(file_path, knowledge_config)
                    except Exception as e:
                        self._file_kb_mapping_dao.update(
                            id=file_id, status=KnowledgeStoreFileStatus.FAIL.value
                        )
                        raise e
                    else:
                        self._file_kb_mapping_dao.update(
                            id=file_id,
                            status=KnowledgeStoreFileStatus.SUCCESS.value,
                            chunk_ids=chunk_ids,
                        )
        else:
            raise ValueError(f"Cannot find file with ID {file_id}.")

    def delete_knowledge(self, file_id: str) -> None:
        """Delete knowledge entry."""
        # get chunk_ids and kb_id with file_id
        file_kb_mapping = self._file_kb_mapping_dao.get_by_id(id=file_id)
        if file_kb_mapping:
            chunk_ids = file_kb_mapping.chunk_ids
            knowledge_base_id = file_kb_mapping.kb_id
            # delete related chunks from knowledge base
            KnowledgeStoreFactory.get_or_create(str(knowledge_base_id)).delete_document(
                str(chunk_ids)
            )
            # delete related file_kb_mapping
            self._file_kb_mapping_dao.delete(id=file_id)
            # delete related virtual file
            FileService.instance.delete_file(id=file_id)
            # update knowledge base timestamp
            self._knowledge_base_dao.update(
                id=str(knowledge_base_id), timestamp=func.strftime("%s", "now")
            )
        else:
            raise ValueError(f"Cannot find knowledge with ID {file_id}.")
