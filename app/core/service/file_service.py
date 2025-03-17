import time
from typing import Any, Dict, List
import os

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
import hashlib
from werkzeug.datastructures import FileStorage

class FileService(metaclass=Singleton):
    """File Service"""

    def __init__(self):
        self._file_dao: FileDAO = FileDAO(DB())
        self._upload_folder = SystemEnv.APP_ROOT + "/uploads"
        if not os.path.exists(self._upload_folder):
            os.makedirs(self._upload_folder)
    
    def calculate_md5(file):
        file_hash = hashlib.md5()
        while chunk := file.read(8192):
            file_hash.update(chunk)
        return file_hash.hexdigest()
    
    def upload_file(
        self, file: FileStorage
    ) -> str:
        """upload a new file.

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
        result = self._dao.create(name=file.filename, path=md5_folder)
        return result.id

    def delete_file(
        self, id
    ):
        """Create a new knowledge base.

        Args:
            name (str): Name of the knowledge base
            knowledge_type (str): Type of the knowledge base
            session_id (str): ID of the session
        """
        # delete the file
        file = self._dao.get_by_id(id=id)
        path = file.path
        results = self._dao.filter_by(file_path=path)
        if len(results == 1):
            for file_name in os.listdir(path):
                file_path = os.path.join(path, file_name)
                os.remove(file_path)
        os.rmdir(path)
