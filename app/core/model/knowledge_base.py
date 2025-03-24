from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class KnowledgeBase:
    """Knowledge class"""

    id: str
    name: str
    knowledge_type: str
    session_id: str
    file_descriptor_list: List[Dict[str, Any]]
    description: str
    timestamp: int


@dataclass
class GlobalKnowledgeBase(KnowledgeBase):
    """Global Knowledge class"""
