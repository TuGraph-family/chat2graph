from dataclasses import dataclass


@dataclass
class KnowledgeBase:
    """KnowledgeBase class"""

    id: str
    name: str
    knowledge_type: str
    session_id: str
