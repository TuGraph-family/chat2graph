from dataclasses import dataclass
from typing import List


@dataclass
class Knowledge:
    """Knowledge class"""

    id: str
    name: str
    knowledge_type: str
    session_id: str
    files: List[str]
    description: str
