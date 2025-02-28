from typing import Optional

from app.core.common.async_func import run_in_thread
from app.core.model.job import Job
from app.core.model.message import ChatMessage
from app.core.model.session import Session
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.service.session_service import SessionService


class SessionWrapper:
    """Facade for managing sessions."""

    def __init__(self, session: Optional[Session] = None):
        session_service: SessionService = SessionService.instance
        self._session: Session = session or session_service.get_session()

    def submit(self, message: ChatMessage) -> JobWrapper:
        """Submit the job."""
        assert self._session, "Session is not set. Please call session() first."
        job = Job(
            goal=message.get_payload(),
            session_id=self._session.id,
            assigned_expert_name=message.get_assigned_expert_name(),
        )
        job_wrapper = JobWrapper(job)

        run_in_thread(job_wrapper.execute)

        return job_wrapper
