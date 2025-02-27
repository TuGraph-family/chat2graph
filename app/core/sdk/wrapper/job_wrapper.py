import time

from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.service.job_service import JobService


class JobWrapper:
    """Facade of the job."""

    def __init__(self, job: Job):
        self._job: Job = job

    @property
    def job(self) -> Job:
        """Get the job."""
        return self._job

    def execute(self):
        """Submit the job."""
        job_service: JobService = JobService.instance
        job_service.execute_job(job=self._job)

    def get_stream(self):
        """Get the stream of the job."""
        # TODO: implement the stream function
        raise NotImplementedError("Stream is not supported yet.")

    def query_result(self) -> JobResult:
        """Get the result of the job."""
        job_service: JobService = JobService.instance
        return job_service.query_job_result(job_id=self._job.id)

    def wait(self, interval: int = 5) -> ChatMessage:
        """Wait for the result."""
        while 1:
            # sleep for `interval` seconds
            time.sleep(interval)

            # query the result every `interval` seconds.
            # please note that the job is executed in the thread,
            # so the result may not be queryed immediately.
            job_result: JobResult = self.query_result()

            # check if the job is finished
            if job_result.has_result():
                return job_result.result
