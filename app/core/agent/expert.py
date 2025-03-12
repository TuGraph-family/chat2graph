from typing import List

from app.core.agent.agent import Agent
from app.core.common.system_env import SystemEnv
from app.core.common.type import WorkflowStatus
from app.core.model.job import Job
from app.core.model.message import AgentMessage, WorkflowMessage
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService


class Expert(Agent):
    """Expert is a role that can execute a workflow."""

    def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> AgentMessage:
        """Execute to resolve the job with enhanced error handling and lesson learned.

        Args:
            job (Job): The job to be executed.

        Returns:
            Job: The job with the response (WorkflowMessage).
        """
        message_service: MessageService = MessageService.instance

        # TODO: convert to a state machine (?)

        job_id = agent_message.get_job_id()
        job_service: JobService = JobService.instance
        job: Job = job_service.get_subjob(job_id=job_id)
        workflow_messages: List[WorkflowMessage] = agent_message.get_workflow_messages()

        workflow_message: WorkflowMessage = self._workflow.execute(
            job=job,
            reasoner=self._reasoner,
            workflow_messages=workflow_messages,
            lesson=agent_message.get_lesson(),
        )

        # save the workflow message in the database
        message_service.save_message(message=workflow_message)

        if workflow_message.status == WorkflowStatus.SUCCESS:
            # (1) WorkflowStatus.SUCCESS
            # color: bright green
            print(f"\033[38;5;46m[Success]: Job {job.id} completed successfully.\033[0m")

            agent_message = AgentMessage(job_id=job.id, workflow_messages=[workflow_message])
            message_service.save_message(message=agent_message)
            return agent_message
        if workflow_message.status == WorkflowStatus.EXECUTION_ERROR:
            # (2) WorkflowStatus.EXECUTION_ERROR

            # color: orange
            print(f"\033[38;5;208m[EXECUTION_ERROR]: Job {job.id} failed.\033[0m")
            print(f"\033[38;5;208mEvaluation: {workflow_message.evaluation}\033[0m")
            print(f"\033[38;5;208mLesson: {workflow_message.lesson}\033[0m")

            # workflow experience -> agent lesson
            agent_message.set_lesson(workflow_message.lesson)

            # retry the job, until the max_retry_count or the job is executed successfully
            max_retry_count = SystemEnv.MAX_RETRY_COUNT
            if retry_count >= max_retry_count:
                raise Exception("The job cannot be executed successfully after retrying.")
            return self.execute(agent_message=agent_message, retry_count=retry_count + 1)
        if workflow_message.status == WorkflowStatus.INPUT_DATA_ERROR:
            # (3) WorkflowStatus.INPUT_DATA_ERROR

            # color: orange
            print(f"\033[38;5;208m[INPUT_DATA_ERROR]: Job {job.id} failed.\033[0m")
            print(f"\033[38;5;208mEvaluation: {workflow_message.evaluation}\033[0m")
            print(f"\033[38;5;208mLesson: {workflow_message.lesson}\033[0m")

            # workflow experience -> agent lesson
            lesson = "The output data is not valid"

            # return the agent message to the leader, and let the leader handle the error
            agent_message = AgentMessage(
                job_id=job.id, workflow_messages=[workflow_message], lesson=lesson
            )
            return agent_message
        if workflow_message.status == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR:
            # (4) WorkflowStatus.JOB_TOO_COMPLICATED_ERROR
            # color: orange
            print(f"\033[38;5;208m[JOB_TOO_COMPLICATED_ERROR]: Job {job.id} failed.\033[0m")
            print(f"\033[38;5;208mEvaluation: {workflow_message.evaluation}\033[0m")
            print(f"\033[38;5;208mLesson: {workflow_message.lesson}\033[0m")

            # return the job to the leader, and let the leader decompose the job
            # workflow experience -> agent lesson
            lesson = "The job is too complicated to be executed by the expert"
            agent_message = AgentMessage(
                job_id=job.id, workflow_messages=[workflow_message], lesson=lesson
            )
            return agent_message
        raise Exception("The workflow status is not defined.")
