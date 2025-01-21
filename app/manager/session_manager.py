import asyncio
from typing import Dict, Optional

from app.agent.core.session import Session
from app.agent.job import Job
from app.agent.job_result import JobResult
from app.common.type import JobStatus
from app.common.util import Singleton
from app.manager.job_manager import JobManager
from app.memory.message import ChatMessage


class SessionManager(metaclass=Singleton):
    """Session manager"""

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    async def create_session(self, session_id: Optional[str] = None) -> Session:
        """Create a session"""
        session = Session(id=session_id) if session_id else Session()
        self._sessions[session.id] = session
        return session

    async def get_session(self, session_id: str) -> Session:
        """Get a session"""
        if session_id not in self._sessions:
            raise ValueError(f"Session with ID {session_id} not found in the session registry.")
        return self._sessions[session_id]

    async def delete_session(self, session_id: str):
        """Delete a session"""
        self._sessions.pop(session_id, None)

    async def submit(self, session_id: str, user_message: ChatMessage) -> Job:
        """Submit the service"""
        if session_id not in self._sessions:
            await self.create_session(session_id=session_id)

        job = Job(
            goal=user_message.get_payload(),
            session_id=session_id,
        )
        await JobManager().submit_job(job=job)

        return job

    async def wait(self, job_id: str, interval: int = 5) -> ChatMessage:
        """Wait for the result"""
        while 1:
            # query the result every n seconds
            job_result: JobResult = await JobManager().query_job_result(job_id=job_id)

            # check if the job is finished
            if job_result.status == JobStatus.FINISHED:
                # print the result
                return job_result.result

            # sleep for `interval` seconds
            await asyncio.sleep(interval)
