import asyncio

from app.agent.job_result import JobResult
from app.memory.message import ChatMessage


class SessionManager:

    async def submit(self, session_id: str,
        user_message: ChatMessage) -> JobResult:
        """Submit the service"""
        asyncio.create_task(
            self._leader.receive_message(user_message=user_message))
