from dataclasses import dataclass
from typing import List

from app.core.model.file_descriptor import FileDescriptor


@dataclass
class KnowledgeBase:
    """Knowledge Store Descriptor class"""

    id: str
    name: str
    knowledge_type: str
    session_id: str
    file_descriptors: List[FileDescriptor]
    description: str
    category: str
    timestamp: int


@dataclass
class GlobalKnowledgeBase(KnowledgeBase):
    """Global Knowledge Store Descriptor class"""
