from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.service.job_service import JobService


class JobWrapper:
    """Facade of the job."""

    def __init__(self, job: Job):
        self._job: Job = job

    @property
    def job(self) -> Job:
        """Get the job."""
        return self._job

    async def execute(self):
        """Submit the job."""
        job_service: JobService = JobService.instance
        await job_service.execute_job(job=self._job)

    async def result(self) -> JobResult:
        """Get the result of the job."""
        job_service: JobService = JobService.instance
        return await job_service.query_job_result(job_id=self._job.id)
