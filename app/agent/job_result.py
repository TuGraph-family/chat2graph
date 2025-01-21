from dataclasses import dataclass

from app.common.type import JobStatus
from app.memory.message import ChatMessage


@dataclass
class JobResult:
    """Job resul

    Attributes:
        job_id (str): the unique identifier of the job.
        status (JobStatus): the status of the job.
        duration (float): the duration of the job execution.
        tokens (int): the LLM tokens consumed by the job.
        result (ChatMessage): the result of the job or the error message.
    """

    job_id: str
    status: JobStatus
    duration: float
    tokens: int
    result: ChatMessage
