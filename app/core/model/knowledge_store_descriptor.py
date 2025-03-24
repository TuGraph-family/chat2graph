from dataclasses import dataclass
from typing import Any, Dict, List

from app.core.model.file_descriptor import FileDescriptor


@dataclass
class KnowledgeStoreDescriptor:
    """Knowledge Store Descriptor class"""

    id: str
    name: str
    knowledge_type: str
    session_id: str
    file_descriptor_list: List[FileDescriptor]
    description: str
    category: str
    timestamp: int


@dataclass
class GlobalKnowledgeStoreDescriptor(KnowledgeStoreDescriptor):
    """Global Knowledge Store Descriptor class"""
