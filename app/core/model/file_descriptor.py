from dataclasses import dataclass
import os


@dataclass
class FileDescriptor:
    """File class"""

    id: str
    name: str
    path: str
    type: str
    size: str
    status: str
    timestamp: int

    def get_payload(self) -> str:
        """Get the content of the file."""
        file_name = os.listdir(self.path)[0]
        file_path = os.path.join(self.path, file_name)
        with open(file_path, encoding="utf-8") as f:
            return f.read()
