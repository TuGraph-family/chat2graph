from typing import Dict, Optional

from app.agent.core.session import Session
from app.agent.job import Job
from app.agent.job_result import JobResult
from app.agent.leader import Leader
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
        return self._sessions.get(session_id)

    async def delete_session(self, session_id: str):
        """Delete a session"""
        self._sessions.pop(session_id, None)

    async def submit(
        self, job_manager: JobManager, leader: Leader, session_id: str, user_message: ChatMessage
    ) -> None:
        """Submit the service"""
        if session_id not in self._sessions:
            self.create_session(session_id=session_id)

        job = Job(
            goal=user_message.get_payload(),
            context=user_message.get_context(),
            session_id=session_id,
        )
        job_manager.submit_job(leader=leader, job=job)

    async def query_state(
        self, job_manager: JobManager, leader: Leader, session_id: str
    ) -> JobResult:
        """Query the result"""
        return await job_manager.query_job_result(leader=leader, job_id=session_id)
