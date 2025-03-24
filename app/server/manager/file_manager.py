from typing import Any, Dict, Tuple

from werkzeug.datastructures import FileStorage

from app.core.service.file_service import FileService


class FileManager:
    """File Manager class to handle business logic"""

    def __init__(self):
        self._file_service: FileService = FileService.instance

    def upload_file(self, file: FileStorage, session_id: str) -> Tuple[Dict[str, Any], str]:
        """Upload a file.

        Args:
            file (FileStorage): file

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing upload status and success message
        """

        file_id = self._file_service.upload_file(file, session_id)
        data = {"file_id": file_id}
        return data, "File uploaded successfully"

    def delete_file(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Dlete file by ID.

        Args:
            id (str): ID of the file

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        self._file_service.delete_file(id)
        data: dict = {}
        return data, "File deleted successfully"
