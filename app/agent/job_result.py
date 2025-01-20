from dataclasses import dataclass

from app.common.type import JobStatus
from app.memory.message import ChatMessage


@dataclass
class JobResult:
    """Job result"""
    job_id: str
    status: JobStatus
    duration: int
    tokens: int
    result: ChatMessage
