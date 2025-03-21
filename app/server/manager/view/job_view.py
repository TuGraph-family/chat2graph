from typing import Any, Dict, TypeVar

from app.core.model.job import Job
from app.core.model.job_result import JobResult

T = TypeVar("T", bound=Job)


class JobView:
    """Job view responsible for transforming internal message models to API response formats."""

    @staticmethod
    def serialize_job_result(job_result: JobResult) -> Dict[str, Any]:
        """Serialize job result object into a dictionary."""
        return {
            "job_id": job_result.job_id,
            "status": job_result.status.value,
            "duration": job_result.duration,
            "tokens": job_result.tokens,
        }
