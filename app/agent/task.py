from abc import ABC
from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4


@dataclass
class Task(ABC):
    """Task in the system."""

    id: str
    content: str
    tags: List[str]

    def __init__(
        self,
        content: str,
        tags: Optional[List[str]] = None,
    ):
        self.id = str(uuid4())
        self.content = content
        self.tags = tags or []
