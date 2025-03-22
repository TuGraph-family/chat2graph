import time
from typing import Any, Dict, List
import os

from app.core.common.singleton import Singleton
from app.core.dal.dao.file_dao import FileDao
from app.core.common.system_env import SystemEnv
import hashlib
from werkzeug.datastructures import FileStorage


class FileService(metaclass=Singleton):
    """File Service"""

    def __init__(self):
        self._file_dao: FileDao = FileDao.instance
        self._upload_folder = SystemEnv.APP_ROOT + "/files"
        if not os.path.exists(self._upload_folder):
            os.makedirs(self._upload_folder)

    def calculate_md5(self, file: FileStorage) -> str:
        file_hash = hashlib.md5()
        while chunk := file.read(8192):
            file_hash.update(chunk)
        return file_hash.hexdigest()

    def upload_file(self, file: FileStorage, session_id: str) -> str:
        """Upload a new file.

        Args:
            name (str): Name of the knowledge base
            knowledge_type (str): Type of the knowledge base
            session_id (str): ID of the session

        Returns:
            str: ID of the file
        """
        # upload the file
        md5_hash = self.calculate_md5(file)
        md5_folder = self._upload_folder + f"/{md5_hash}/"
        if not os.path.exists(md5_folder):
            os.makedirs(md5_folder)
            file_path = os.path.join(md5_folder, file.filename)
            file.seek(0)
            file.save(file_path)
        result = self._file_dao.create(
            name=file.filename, path=md5_folder, type="local", session_id=session_id
        )
        return str(result.id)

    def delete_file(self, id: str) -> None:
        """Delete a file with ID.

        Args:
            name (str): Name of the knowledge base
            knowledge_type (str): Type of the knowledge base
            session_id (str): ID of the session
        """
        # delete the file
        file = self._file_dao.get_by_id(id=id)
        if file:
            path = file.path
            self._file_dao.delete(id=id)
            results = self._file_dao.filter_by(path=path)
            if len(results) == 0:
                for file_name in os.listdir(path):
                    file_path = os.path.join(path, file_name)
                    os.remove(file_path)
                os.rmdir(path)
        else:
            raise ValueError(f"Cannot find file with ID {id}.")

    def get_file_payload(self, id: str) -> str:
        file = self._file_dao.get_by_id(id=id)
        if file:
            path = file.path
            file_name = os.listdir(path)[0]
            file_path = os.path.join(path, file_name)
            with open(file_path, "r") as f:
                return f.read()
        else:
            raise ValueError(f"Cannot find file with ID {id}.")
