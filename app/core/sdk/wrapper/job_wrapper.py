from app.core.model.job import Job
from app.core.model.job_graph import JobGraph
from app.core.model.job_result import JobResult
from app.core.service.job_service import JobService


class JobWrapper:
    """Facade of the job graph.

    The JobWrapper can only be used to retrieve the job graph rather than
    modifying it. The job graph is a directed acyclic graph (DAG) that
    represents the job execution flow of the agentic system.
    """

    def __init__(self):
        self._job_service: JobService = JobService.instance or JobService()

    def get_job_graph(self, id: str) -> JobGraph:
        """Get the job graph by id."""
        return self._job_service.get_job_graph(job_id=id)

    def get_job(self, original_job_id: str, job_id: str) -> Job:
        """Get the job by original job id."""
        return self._job_service.get_job(original_job_id=original_job_id, job_id=job_id)

    async def execute_job(self, job: Job) -> None:
        """Execute the job."""
        await self._job_service.execute_job(job=job)

    async def query_job_result(self, id: str) -> JobResult:
        """Query the result of the multi-agent system by original job id."""
        return await self._job_service.query_job_result(job_id=id)
