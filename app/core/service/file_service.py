import hashlib
import os

from werkzeug.datastructures import FileStorage

from app.core.common.singleton import Singleton
from app.core.common.system_env import SystemEnv
from app.core.dal.dao.file_descriptor_dao import FileDescriptorDao
from app.core.model.file_descriptor import FileDescriptor
from app.core.common.type import KnowledgeStoreFileStatus, FileStorageType


class FileService(metaclass=Singleton):
    """File Service"""

    def __init__(self):
        self._file_descriptor_dao: FileDescriptorDao = FileDescriptorDao.instance
        self._upload_folder = SystemEnv.APP_ROOT + "/files"
        if not os.path.exists(self._upload_folder):
            os.makedirs(self._upload_folder)

    def calculate_md5(self, file: FileStorage) -> str:
        """Calculate the MD5 hash of a file."""
        file_hash = hashlib.md5()
        while chunk := file.read(8192):
            file_hash.update(chunk)
        return file_hash.hexdigest()

    def upload_file(self, file: FileStorage, session_id: str) -> str:
        """Upload a new file.

        Args:
            file (FileStorage): file
            session_id (str): ID of the session

        Returns:
            str: ID of the file
        """
        md5_hash = self.calculate_md5(file)
        md5_folder = self._upload_folder + f"/{md5_hash}/"
        if not os.path.exists(md5_folder):
            os.makedirs(md5_folder)
            file_path = os.path.join(md5_folder, file.filename)
            file.seek(0)
            file.save(file_path)
        file_path = os.path.join(md5_folder, os.listdir(md5_folder)[0])
        result = self._file_descriptor_dao.create(
            name=file.filename,
            path=md5_folder,
            type=FileStorageType.LOCAL.value,
            session_id=session_id,
            size=os.path.getsize(file_path),
        )
        return str(result.id)

    def delete_file(self, id: str) -> None:
        """Delete a file with ID.

        Args:
            file (FileStorage): file
            session_id (str): ID of the session
        """
        file_do = self._file_descriptor_dao.get_by_id(id=id)
        if file_do:
            path = file_do.path
            self._file_descriptor_dao.delete(id=id)
            results = self._file_descriptor_dao.filter_by(path=path)
            if len(results) == 0:
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    os.remove(file_path)
                os.rmdir(path)
        else:
            raise ValueError(f"Cannot find file with ID {id}.")

    def get_file_descriptor(self, file_id: str) -> FileDescriptor:
        """Get the content of a file with ID.

        Args:
            file_id (str): ID of the file
        """
        file_do = self._file_descriptor_dao.get_by_id(id=file_id)
        if file_do:
            return FileDescriptor(
                id=file_id,
                path=str(file_do.path),
                name=str(file_do.name),
                type=FileStorageType(file_do.path),
                size=str(file_do.size),
                status=KnowledgeStoreFileStatus.SUCCESS,
                timestamp=int(file_do.timestamp),
            )
        raise ValueError(f"Cannot find file with ID {id}.")
