from dataclasses import dataclass
import os


@dataclass
class FileDescriptor:
    """File class"""

    def __init__(self, id: str, name: str, path: str, type: str, session_id: str, size: str, status: str, timestamp: int):
        self._id = id
        self._name = name
        self._path = path
        self._type = type
        self.size = size
        self._session_id = session_id
        self._status = status
        self._timestamp = timestamp

    def get_payload(self) -> str:
        """Get the content of the file."""
        file_name = os.listdir(self._path)[0]
        file_path = os.path.join(self._path, file_name)
        with open(file_path, encoding="utf-8") as f:
            return f.read()
