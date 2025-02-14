import asyncio
from typing import Optional, Tuple

from app.core.common.type import JobStatus
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.service.job_service import JobService
from app.core.service.session_service import SessionService


class SessionWrapper:
    """Facade for managing sessions."""

    def __init__(self):
        self._session_service: SessionService = SessionService.instance or SessionService()

    def session(self, session_id: Optional[str] = None) -> Tuple["SessionWrapper", str]:
        """Set the session ID."""
        return self, self._session_service.get_session(session_id=session_id).id

    async def submit(self, session_id: str, message: ChatMessage) -> Job:
        """Submit the job."""
        job = Job(goal=message.get_payload(), session_id=session_id)
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
