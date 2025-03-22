from dataclasses import dataclass
from typing import List

class File:
    """File class"""

    def __init__(
        self,
        id: str,
        name: str,
        path: str,
        type: str,
        session_id: str,
    ):
        self._id = id
        self._name = name
        self._path = path
        self._type = type
        self._session_id = session_id
    
    def get_payload(self) -> str:
        """Get the content of the file."""
        return ""
