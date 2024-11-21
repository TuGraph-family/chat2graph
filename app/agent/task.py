from abc import ABC
from typing import List, Optional
from uuid import uuid4


class Task(ABC):
    """The task in the system."""

    def __init__(
        self,
        content: str,
        tags: Optional[List[str]] = None,
    ):
        self.id = str(uuid4())
        self.content = content
        self.tags = tags or []
