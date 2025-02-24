import asyncio
from typing import Optional

from app.core.common.type import JobStatus
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.model.session import Session
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.service.session_service import SessionService


class SessionWrapper:
    """Facade for managing sessions."""

    def __init__(self):
        self._session: Optional[Session] = None

    def session(self, session_id: Optional[str] = None) -> "SessionWrapper":
        """Set the session ID."""
        session_service: SessionService = SessionService.instance
        self._session = session_service.get_session(session_id=session_id)
        return self

    async def submit(self, message: ChatMessage) -> JobWrapper:
        """Submit the job."""
        assert self._session, "Session is not set. Please call session() first."
        job = Job(
            goal=message.get_payload(),
            session_id=self._session.id,
            assigned_expert_name=message.get_assigned_expert_name(),
        )
        job_wrapper = JobWrapper(job)

        asyncio.create_task(job_wrapper.execute())

        return job_wrapper

    async def wait(self, job_wrapper: JobWrapper, interval: int = 5) -> ChatMessage:
        """Wait for the result."""
        while 1:
            # sleep for `interval` seconds
            await asyncio.sleep(interval)

            # query the result every `interval` seconds.
            # please note that the job is executed asynchronously,
            # so the result may not be queryed immediately.
            job_result: JobResult = await job_wrapper.result()

            # check if the job is finished
            if job_result.status == JobStatus.FINISHED:
                return job_result.result
