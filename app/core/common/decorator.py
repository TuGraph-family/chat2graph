import asyncio

from app.core.common.type import JobStatus
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.service.job_service import JobService


def session_wrapper(cls):
    """Decorator for the session wrapper."""

    class SessionWrapper(cls):
        """Session Wrapper class"""

        async def submit(self, message: ChatMessage) -> Job:
            """Submit the job."""

            job = Job(goal=message.get_payload(), session_id=self.id)
            job_service: JobService = JobService.instance
            asyncio.create_task(job_service.execute_job(job=job))

            return job

        async def wait(self, job_id: str, interval: int = 5) -> ChatMessage:
            """Wait for the result."""
            while 1:
                # sleep for `interval` seconds
                await asyncio.sleep(interval)

                # query the result every `interval` seconds.
                # please note that the job is executed asynchronously,
                # so the result may not be queryed immediately.
                job_service: JobService = JobService.instance
                job_result: JobResult = await job_service.query_job_result(job_id=job_id)

                # check if the job is finished
                if job_result.status == JobStatus.FINISHED:
                    return job_result.result

    return SessionWrapper
