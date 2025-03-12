from dataclasses import dataclass


@dataclass
class Knowledge:
    """Knowledge class"""

    id: str
    name: str
    knowledge_type: str
    session_id: str
