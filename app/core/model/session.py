from dataclasses import dataclass
from typing import Optional


@dataclass
class Session:
    """Session class"""

    id: str
    name: Optional[str]
    timestamp: Optional[int]

    # the latest job id of the session
    latest_job_id: Optional[str] = None
