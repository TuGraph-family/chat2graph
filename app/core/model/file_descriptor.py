from dataclasses import dataclass
import os
from typing import Optional
from app.core.common.type import KnowledgeStoreFileStatus, FileStorageType


@dataclass
class FileDescriptor:
    """File class"""

    id: str
    name: str
    path: Optional[str]
    type: FileStorageType
    size: str
    status: KnowledgeStoreFileStatus
    timestamp: int

    def get_payload(self) -> str:
        """Get the content of the file."""
        if self.path:
            file_name = os.listdir(self.path)[0]
            file_path = os.path.join(self.path, file_name)
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        else:
            return ""
