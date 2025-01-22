import asyncio

from app.agent.job import Job
from app.agent.job_result import JobResult
from app.common.type import JobStatus
from app.manager.job_manager import JobManager
from app.memory.message import ChatMessage


def job_submit(cls):
    """Decorator for the job submit session."""

    class JobSubmitSession(cls):
        """Job submit session"""

        async def submit(self, user_message: ChatMessage) -> Job:
            """Submit the job."""

            job = Job(
                goal=user_message.get_payload(),
                session_id=self.id,
            )
            await JobManager().submit_job(job=job)
            return job

        async def wait(self, job_id: str, interval: int = 5) -> ChatMessage:
            """Wait for the result."""
            while 1:
                # query the result every n seconds
                job_result: JobResult = await JobManager().query_job_result(job_id=job_id)

                # check if the job is finished
                if job_result.status == JobStatus.FINISHED:
                    # print the result
                    return job_result.result

                # sleep for `interval` seconds
                await asyncio.sleep(interval)

    return JobSubmitSession
