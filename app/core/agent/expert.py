import traceback
from typing import List

from app.core.agent.agent import Agent
from app.core.common.system_env import SystemEnv
from app.core.common.type import JobStatus, WorkflowStatus
from app.core.model.job import SubJob
from app.core.model.job_result import JobResult
from app.core.model.message import AgentMessage, MessageType, WorkflowMessage
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
        job_service: JobService = JobService.instance

        # TODO: convert to a state machine (?)

        # get the job from the agent message
        job_id = agent_message.get_job_id()
        job: SubJob = job_service.get_subjob(subjob_id=job_id)

        # get the workflow messages from the agent message
        workflow_messages: List[WorkflowMessage] = agent_message.get_workflow_messages()

        # update the job status to running
        job_result = job_service.get_job_result(job_id=job.id)
        job_result.status = JobStatus.RUNNING
        job_service.save_job_result(job_result=job_result)

        # execute the workflow of the expert
        try:
            workflow_message: WorkflowMessage = self._workflow.execute(
                job=job,
                reasoner=self._reasoner,
                workflow_messages=workflow_messages,
                lesson=agent_message.get_lesson(),
            )
        except Exception as e:
            workflow_message = WorkflowMessage(
                payload={
                    "scratchpad": str(e) + "\n" + traceback.format_exc(),
                    "status": WorkflowStatus.EXECUTION_ERROR,
                    "evaluation": "There occurs some errors during the execution: "
                    f"{str(e)}\n{traceback.format_exc()}",
                    "lesson": "",  # TODO: add the lesson learned
                },
            )

        # save the workflow message in the database
        message_service.save_message(message=workflow_message)

        if workflow_message.status == WorkflowStatus.SUCCESS:
            # (1) WorkflowStatus.SUCCESS
            # color: bright green
            print(f"\033[38;5;46m[Success]: Job {job.id} completed successfully.\033[0m")

            # (1.1) save the expert message in the database
            try:
                existed_expert_message = message_service.get_message_by_job_id(
                    job_id=job.id, message_type=MessageType.AGENT_MESSAGE
                )[0]
                expert_message = AgentMessage(
                    id=existed_expert_message.get_id(),
                    job_id=job.id,
                    workflow_messages=[workflow_message],
                    payload=workflow_message.scratchpad,
                )
            except Exception:
                # if the agent message is not found, create a new agent message
                expert_message = AgentMessage(
                    job_id=job.id,
                    workflow_messages=[workflow_message],
                    payload=workflow_message.scratchpad,
                )
            message_service.save_message(message=expert_message)

            # (1.2) save the job result in the database
            job_result = job_service.get_job_result(job_id=job.id)
            job_result.status = JobStatus.FINISHED
            job_service.save_job_result(job_result=job_result)

            return expert_message
        if workflow_message.status == WorkflowStatus.EXECUTION_ERROR:
            # (2) WorkflowStatus.EXECUTION_ERROR

            # color: orange
            print(f"\033[38;5;208m[EXECUTION_ERROR]: Job {job.id} failed.\033[0m")
            print(f"\033[38;5;208mEvaluation: {workflow_message.evaluation}\033[0m")
            print(f"\033[38;5;208mLesson: {workflow_message.lesson}\033[0m")

            # workflow experience -> agent lesson
            lesson = workflow_message.evaluation + "\n" + workflow_message.lesson
            agent_message.add_lesson(lesson)

            # retry the job, until the max_retry_count or the job is executed successfully
            max_retry_count = SystemEnv.MAX_RETRY_COUNT
            if retry_count >= max_retry_count:
                # (2.1) save the expert message in the database
                message_service.save_message(message=agent_message)

                # (2.2) save the expert message in the database
                try:
                    job_result = job_service.get_job_result(job_id=job.id)
                    job_result.status = JobStatus.FAILED
                except Exception:
                    # if the job result is not found, create a new job result
                    job_result = JobResult(
                        job_id=job.id,
                        status=JobStatus.FAILED,
                        duration=0,  # TODO: calculate the duration
                        tokens=0,  # TODO: calculate the tokens
                    )
                job_service.save_job_result(job_result=job_result)

                raise Exception(
                    "The job cannot be executed successfully "
                    "after retrying {max_retry_count} times."
                )
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
            # (3.1) save the expert message in the database
            try:
                existed_expert_message = message_service.get_message_by_job_id(
                    job_id=job.id, message_type=MessageType.AGENT_MESSAGE
                )[0]
                expert_message = AgentMessage(
                    id=existed_expert_message.get_id(),
                    job_id=job.id,
                    workflow_messages=[workflow_message],
                    lesson=lesson,
                    payload=workflow_message.scratchpad,
                )
            except Exception:
                expert_message = AgentMessage(
                    job_id=job.id,
                    workflow_messages=[workflow_message],
                    lesson=lesson,
                    payload=workflow_message.scratchpad,
                )
            message_service.save_message(message=expert_message)

            return expert_message
        if workflow_message.status == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR:
            # (4) WorkflowStatus.JOB_TOO_COMPLICATED_ERROR
            # color: orange
            print(f"\033[38;5;208m[JOB_TOO_COMPLICATED_ERROR]: Job {job.id} failed.\033[0m")
            print(f"\033[38;5;208mEvaluation: {workflow_message.evaluation}\033[0m")
            print(f"\033[38;5;208mLesson: {workflow_message.lesson}\033[0m")

            # return the job to the leader, and let the leader decompose the job
            # workflow experience -> agent lesson
            # (4.1) save the expert message in the database
            lesson = "The job is too complicated to be executed by the expert"
            try:
                existed_expert_message = message_service.get_message_by_job_id(
                    job_id=job.id, message_type=MessageType.AGENT_MESSAGE
                )[0]
                expert_message = AgentMessage(
                    id=existed_expert_message.get_id(),
                    job_id=job.id,
                    workflow_messages=[workflow_message],
                    lesson=lesson,
                    payload=workflow_message.scratchpad,
                )
            except Exception:
                expert_message = AgentMessage(
                    job_id=job.id,
                    workflow_messages=[workflow_message],
                    lesson=lesson,
                    payload=workflow_message.scratchpad,
                )
            message_service.save_message(message=expert_message)

            return expert_message
        raise Exception("The workflow status is not defined.")
