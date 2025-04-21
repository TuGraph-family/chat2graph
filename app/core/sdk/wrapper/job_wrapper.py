import time
from typing import cast

from app.core.common.type import ChatMessageRole
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage, HybridMessage
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService


class JobWrapper:
    """Facade of the job."""

    def __init__(self, job: Job):
        self._job: Job = job

    @property
    def job(self) -> Job:
        """Get the job."""
        return self._job

    @property
    def id(self) -> str:
        """Get the job id."""
        return self._job.id

    def execute(self):
        """Submit the job."""
        agent_service: AgentService = AgentService.instance
        agent_service.leader.execute_original_job(original_job=self._job)

    def get_stream(self):
        """Get the stream of the job."""
        # TODO: implement the stream function
        raise NotImplementedError("Stream is not supported yet.")

    def wait(self, interval: int = 5) -> ChatMessage:
        """Wait for the result."""
        while 1:
            # sleep for `interval` seconds
            time.sleep(interval)

            # query the result every `interval` seconds.
            # please note that the job is executed in the thread,
            # so the result may not be queryed immediately.
            job_service: JobService = JobService.instance
            job_result: JobResult = job_service.query_original_job_result(
                original_job_id=self._job.id
            )

            # check if the job is finished
            if job_result.has_result():
                message_service: MessageService = MessageService.instance
                return cast(
                    HybridMessage,
                    message_service.get_hybrid_message_by_job_id_and_role(
                        job_id=self._job.id,
                        role=ChatMessageRole.SYSTEM,
                    ),
                )
