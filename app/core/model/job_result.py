from dataclasses import dataclass

from app.core.common.type import JobStatus


@dataclass
class JobResult:
    """Job result data class.

    Attributes:
        job_id (str): the unique identifier of the job.
        status (JobStatus): the status of the job.
        duration (float): the duration of the job execution.
        tokens (int): the LLM tokens consumed by the job.
    """

    job_id: str
    status: JobStatus
    duration: float = 0.0
    tokens: int = 0

    def has_result(self) -> bool:
        """Check if the job has result."""
        return self.status in [JobStatus.FINISHED, JobStatus.FAILED, JobStatus.STOPPED]
