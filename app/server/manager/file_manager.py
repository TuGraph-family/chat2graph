from enum import Enum
from typing import Any, Dict, List, Tuple

from app.core.service.file_service import FileService
from app.core.service.session_service import SessionService
from app.server.common.util import ServiceException
from werkzeug.datastructures import FileStorage

class KnowledgeBaseManager:
    """Knowledge Base Manager class to handle business logic"""

    def __init__(self):
        self._file_service: FileService = FileService.instance

    def upload_file(
        self, file: FileStorage
    ) -> Tuple[Dict[str, Any], str]:
        """Upload a file.

        Args:
            file (FileStorage): file
        
        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing upload status and success message
        """

        try:
            file_id = self._file_service.upload_file(file)
            data = {"file_id": file_id}
            return data, "File uploaded successfully"
        except Exception as e:
            raise ServiceException(f"Failed to upload file: {str(e)}") from e

    def delete_file(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Dlete file by ID.

        Args:
            id (str): ID of the file
        
        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        try:
            self._file_service.delete_file(id)
            data = {}
            return data, "File deleted successfully"
        except Exception as e:
            raise ServiceException(f"Failed to delete file: {str(e)}") from e
