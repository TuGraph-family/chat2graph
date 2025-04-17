import hashlib
import os
from typing import Optional

from werkzeug.datastructures import FileStorage

from app.core.common.singleton import Singleton
from app.core.common.system_env import SystemEnv
from app.core.common.type import FileStorageType, KnowledgeStoreFileStatus
from app.core.dal.dao.file_descriptor_dao import FileDescriptorDao
from app.core.model.file_descriptor import FileDescriptor


class FileService(metaclass=Singleton):
    """File Service"""

    def __init__(self):
        self._file_descriptor_dao: FileDescriptorDao = FileDescriptorDao.instance
        self._upload_folder: str = SystemEnv.APP_ROOT + SystemEnv.FILE_PATH
        if not os.path.exists(self._upload_folder):
            os.makedirs(self._upload_folder)

    def _calculate_md5(self, file: FileStorage) -> str:
        """Calculate the MD5 hash of a file."""
        file_hash = hashlib.md5()
        while chunk := file.read(8192):
            file_hash.update(chunk)
        return file_hash.hexdigest()

    def upload_or_update_file(self, file: FileStorage, file_id: Optional[str] = None) -> str:
        """Upload a new file or update an existing file with the file id.

        Args:
            file (FileStorage): file
            file_id (Optional[str]): ID of the file to update. If provided and exists,
                the file with this ID will be updated.
                If not provided or not found, a new file will be created.

        Returns:
            str: ID of the file
        """
        md5_hash = self._calculate_md5(file)
        md5_folder = self._upload_folder + f"/{md5_hash}/"
        if not os.path.exists(md5_folder):
            os.makedirs(md5_folder)

        # save the file
        file_path = os.path.join(md5_folder, file.filename)
        file.seek(0)
        file.save(file_path)

        if file_id:
            existing_file_do = self._file_descriptor_dao.get_by_id(id=file_id)
            if existing_file_do:
                # remove the old file
                old_path = existing_file_do.path
                old_file_path = os.path.join(old_path, existing_file_do.name)

                # check if there is any other record using the same flolder
                other_records = self._file_descriptor_dao.filter_by(path=old_path)
                other_records = [r for r in other_records if r.id != file_id]

                # if the old path is different from the new one and no other records using it
                if old_path != md5_folder and len(other_records) == 0:
                    try:
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)
                        if os.path.exists(old_path) and len(os.listdir(old_path)) == 0:
                            os.rmdir(old_path)
                    except Exception:
                        print(
                            "Warning: Failed to update the file storage, "
                            f"when removing the {old_file_path}. "
                        )

                # update existing file record
                self._file_descriptor_dao.update(
                    id=file_id,
                    name=file.filename,
                    path=md5_folder,
                    type=FileStorageType.LOCAL.value,
                    size=os.path.getsize(file_path),
                )
                return file_id

        # create new file record
        result = self._file_descriptor_dao.create(
            id=file_id,  # allow id to be None for new records
            name=file.filename,
            path=md5_folder,
            type=FileStorageType.LOCAL.value,
            size=os.path.getsize(file_path),
        )
        return str(result.id)

    def delete_file(self, id: str) -> None:
        """Delete a file with ID.

        Args:
            file (FileStorage): file
        """
        file_descriptor_do = self._file_descriptor_dao.get_by_id(id=id)
        if file_descriptor_do:
            path = file_descriptor_do.path
            self._file_descriptor_dao.delete(id=id)
            results = self._file_descriptor_dao.filter_by(path=path)
            if len(results) == 0:
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    os.remove(file_path)
                os.rmdir(path)
        else:
            raise ValueError(f"Cannot find file with ID {id}.")

    def read_file(self, file_id: str) -> str:
        """Read the content of a file with ID and return it as a string."""
        file_do = self._file_descriptor_dao.get_by_id(id=file_id)
        if file_do:
            file_path = os.path.join(file_do.path, file_do.name)
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        raise ValueError(f"Cannot find file with ID {id}.")

    def get_file_descriptor(self, file_id: str) -> FileDescriptor:
        """Get the content of a file with ID.

        Args:
            file_id (str): ID of the file
        """
        file_descriptor_do = self._file_descriptor_dao.get_by_id(id=file_id)
        if file_descriptor_do:
            return FileDescriptor(
                id=file_id,
                path=str(file_descriptor_do.path),
                name=str(file_descriptor_do.name),
                type=FileStorageType(str(file_descriptor_do.type)),
                size=str(file_descriptor_do.size),
                status=KnowledgeStoreFileStatus.SUCCESS,
                timestamp=int(file_descriptor_do.timestamp),
            )
        raise ValueError(f"Cannot find file with ID {id}.")
