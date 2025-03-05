from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Session:
    """Session class"""

    id: str
    name: Optional[str] = None
    # TOOD: replace to timpstamps string
    created_at: Optional[datetime] = None
