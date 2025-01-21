from typing import Optional
from uuid import uuid4

from app.agent.job import Job
from app.agent.job_result import JobResult
from app.agent.leader import Leader
from app.manager.job_manager import JobManager
from app.memory.message import ChatMessage


class Session:
    """Session"""

    def __init__(self, id: Optional[str] = None):
        self.id: str = id or str(uuid4())

    async def submit(
        self, job_manager: JobManager, leader: Leader, session_id: str, user_message: ChatMessage
    ) -> JobResult:
        """Submit the service"""
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
