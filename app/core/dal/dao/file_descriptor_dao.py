from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.common.type import FileStorageType, KnowledgeStoreFileStatus
from app.core.dal.dao.dao import Dao
from app.core.dal.do.file_descriptor_do import FileDescriptorDo
from app.core.model.file_descriptor import FileDescriptor


class FileDescriptorDao(Dao[FileDescriptorDo]):
    """File descriptor Data Access Object"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(FileDescriptorDo, session)

    def get_file_descriptor_by_id(self, id: str) -> FileDescriptor:
        """Get a file descriptor by ID."""
        file_descriptor_do = self.get_by_id(id=id)
        if not file_descriptor_do:
            raise ValueError(f"File descriptor with ID {id} not found")
        return FileDescriptor(
            id=str(file_descriptor_do.id),
            name=str(file_descriptor_do.name),
            path=str(file_descriptor_do.path),
            type=FileStorageType(str(file_descriptor_do.type)),
            size=str(file_descriptor_do.size),
            status=KnowledgeStoreFileStatus.SUCCESS,  # TODO: fix this (file_descriptor_do.status)
            timestamp=int(file_descriptor_do.timestamp),
        )
