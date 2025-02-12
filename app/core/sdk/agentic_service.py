from typing import Optional

from app.core.common.singleton import Singleton
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.model.session import Session
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.session_service import SessionService


class AgenticService(metaclass=Singleton):
    """Agentic service class"""

    def __init__(self):
        # TODO: configure the chat2graph service by yaml

        # initialize the leader service
        self._agent_service = AgentService()

        # initialize the job service
        self._job_service = JobService()

        # initialize the session service
        self._session_service = SessionService()

    def session(self, session_id: Optional[str] = None) -> Session:
        """Get the session, if not exists or session_id is None, create a new one."""
        return SessionService().get_session(session_id=session_id)

    async def execute(self, message: ChatMessage) -> ChatMessage:
        """Execute the service synchronously."""
        job = Job(goal=message.get_payload())
        await self._job_service.execute_job(job=job)

        job_result: JobResult = await self._job_service.query_job_result(job_id=job.id)
        return job_result.result
