from app.agent.job_result import JobResult


class JobManager:

    async def query_job_result(self, session_id: str, job_id: str) -> JobResult:
        """Query the result"""
        return await self._leader.query_state(session_id=session_id)
