from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    """Session class"""

    id: str
    name: Optional[str]
    timestamp: Optional[int]
