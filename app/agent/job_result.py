from dataclasses import dataclass

from app.common.type import JobStatus
from app.memory.message import ChatMessage


@dataclass
class JobResult:
    """Job resul

    Attributes:
        job_id (str): the unique identifier of the job.
        status (JobStatus): the status of the job.
        result (ChatMessage): the result of the job or the error message.
        duration (float): the duration of the job execution.
        tokens (int): the LLM tokens consumed by the job.
    """

    job_id: str
    status: JobStatus
    result: ChatMessage
    duration: float = 0.0
    tokens: int = 0
