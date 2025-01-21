import asyncio
import time
from typing import Dict

from app.agent.job import Job
from app.agent.job_result import JobResult
from app.agent.leader import Leader
from app.common.type import JobStatus
from app.common.util import Singleton
from app.memory.message import ChatMessage


class JobManager(metaclass=Singleton):
    """Job manager"""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}  # job_id -> job (main job)
        self._job_results: Dict[str, JobResult] = {}  # job_id -> job_result

    async def execute_job(self, job: Job) -> JobResult:
        """Execute the job"""

        await Leader().receive_submission(job=job)
        return await self.query_job_result(job_id=job.id)

    async def submit_job(self, job: Job) -> None:
        """Submit the job"""
        self._jobs[job.id] = job
        asyncio.create_task(Leader().receive_submission(job=job))

    async def query_job_result(self, job_id: str) -> JobResult:
        """Query the result of the multi-agent system."""
        if job_id not in self._jobs:
            raise ValueError(f"Job with ID {job_id} not found in the job registry.")
        if job_id in self._job_results:
            return self._job_results[job_id]

        # query the state to get the job execution information
        job_graph = Leader().get_leader_state().get_job_graph(main_job_id=job_id)

        # get the tail nodes of the job graph (DAG)
        tail_nodes = [node for node in job_graph.nodes if job_graph.out_degree(node) == 0]
        mutli_agent_content = ""
        for tail_node in tail_nodes:
            workflow_result = job_graph.nodes[tail_node]["workflow_result"]
            if not workflow_result:
                chat_message = ChatMessage(
                    content="The job is not completed yet.",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                )
                job_result = JobResult(
                    job_id=job_id,
                    status=JobStatus.RUNNING,
                    duration=0,  # TODO: calculate the duration
                    tokens=0,  # TODO: calculate the tokens
                    result=chat_message,
                )
            mutli_agent_content += job_graph.nodes[tail_node]["workflow_result"].scratchpad + "\n"
        chat_message = ChatMessage(
            content=mutli_agent_content,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        job_result = JobResult(
            job_id=job_id,
            status=JobStatus.FAILED,
            duration=0,  # TODO: calculate the duration
            tokens=0,  # TODO: calculate the tokens
            result=chat_message,
        )

        # update the job result in the job results registry
        self._job_results[job_id] = job_result

        return job_result
