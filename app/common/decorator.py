import asyncio

from app.agent.graph import JobGraph
from app.agent.job import Job
from app.agent.job_result import JobResult
from app.agent.leader import Leader
from app.common.type import JobStatus
from app.manager.job_manager import JobManager
from app.memory.message import ChatMessage


def session_wrapper(cls):
    """Decorator for the session wrapper."""

    class SessionWraper(cls):
        """Session Wrapper class"""

        async def submit(self, message: ChatMessage) -> Job:
            """Submit the job."""

            job = Job(goal=message.get_payload(), session_id=self.id)
            job_graph: JobGraph = JobGraph()
            job_graph.add_node(id=job.id, job=job)
            JobManager().set_job_graph(job_id=job.id, job_graph=job_graph)
            asyncio.create_task(Leader().receive_submission(job=job))

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

    return SessionWraper
