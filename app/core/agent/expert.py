import traceback
from typing import List, cast

from app.core.agent.agent import Agent
from app.core.common.system_env import SystemEnv
from app.core.common.type import JobStatus, WorkflowStatus
from app.core.model.job import SubJob
from app.core.model.message import AgentMessage, MessageType, WorkflowMessage


class Expert(Agent):
    """Expert is a role that can execute a workflow."""

    def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> AgentMessage:
        """Execute to resolve the job with enhanced error handling and lesson learned.

        Args:
            agent_message (AgentMessage): The message from the agent containing
                the job to be executed.
            retry_count (int): The number of times the job has been retried. Defaults to 0.

        Returns:
            AgentMessage: The message containing the result of the job execution,
                which includes the workflow message and any lessons learned.
        """
        # TODO: convert to a state machine (?)

        # get the job from the agent message
        job_id = agent_message.get_job_id()
        job: SubJob = self._job_service.get_subjob(subjob_id=job_id)

        # update the job status to running
        job_result = self._job_service.get_job_result(job_id=job.id)
        if job_result.has_result():
            # if the job result already has a final status, do not execute again

            if job_result.status == JobStatus.FINISHED:
                # color: green
                print(
                    f"\033[38;5;46m[Success]: Job {job.id} already completed successfully.\033[0m"
                )
                return cast(
                    AgentMessage,
                    self._message_service.get_message_by_job_id(
                        job_id=job.id,
                        message_type=MessageType.AGENT_MESSAGE,
                    )[0],
                )

            # color: orange
            print(
                f"\033[38;5;208m[Warning]: Job {job.id} already has a final status: "
                f"{job_result.status.value}.\033[0m"
            )
            if self._workflow.evaluator:
                return self.save_output_agent_message(
                    job=job,
                    workflow_message=WorkflowMessage(
                        payload={
                            "scratchpad": f"Job {job.id} already has a final status: "
                            f"{job_result.status.value}.",
                            "evaluation": "No further execution needed.",
                            "lesson": "",  # no lesson to add since it already has a final status
                        },
                        job_id=job.id,
                    ),
                )
            # if there is no evaluator, return the existing job result
            return self.save_output_agent_message(
                job=job,
                workflow_message=WorkflowMessage(
                    payload={
                        "scratchpad": f"Job {job.id} already has a final status: "
                        f"{job_result.status.value}.",
                    },
                    job_id=job.id,
                ),
            )
        job_result.status = JobStatus.RUNNING
        self._job_service.save_job_result(job_result=job_result)

        # get the workflow messages from the agent message
        workflow_messages: List[WorkflowMessage] = agent_message.get_workflow_messages()

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
                    "scratchpad": f"The current job {job.id} failed: "
                    f"{str(e)}\n{traceback.format_exc()}\n",
                    "status": WorkflowStatus.EXECUTION_ERROR,
                    "evaluation": f"There occurs some errors during the execution: {str(e)}",
                    "lesson": "",
                },
            )

        # save the workflow message in the database
        self._message_service.save_message(message=workflow_message)

        if workflow_message.status == WorkflowStatus.SUCCESS:
            # (1) WorkflowStatus.SUCCESS
            # (1.1) save the expert message in the database
            expert_message = self.save_output_agent_message(
                job=job, workflow_message=workflow_message
            )

            # (1.2) save the job result in the database
            job_result = self._job_service.get_job_result(job_id=job.id)
            if not job_result.has_result():
                job_result.status = JobStatus.FINISHED
                self._job_service.save_job_result(job_result=job_result)

                # color: bright green
                print(f"\033[38;5;46m[Success]: Job {job.id} completed successfully.\033[0m")

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
                expert_message = self.save_output_agent_message(
                    job=job, workflow_message=workflow_message, lesson=lesson
                )

                # (2.2) do not mark the job as failed, but return the expert message, since leader
                # will handle the error, and fail the job graph
                # job_result = self._job_service.get_job_result(job_id=job.id)
                # job_result.status = JobStatus.FAILED
                # self._job_service.save_job_result(job_result=job_result)
                return expert_message
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
            expert_message = self.save_output_agent_message(
                job=job, workflow_message=workflow_message, lesson=lesson
            )

            return expert_message
        if workflow_message.status == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR:
            # (4) WorkflowStatus.JOB_TOO_COMPLICATED_ERROR
            # color: orange
            print(f"\033[38;5;208m[JOB_TOO_COMPLICATED_ERROR]: Job {job.id} failed.\033[0m")
            print(f"\033[38;5;208mEvaluation: {workflow_message.evaluation}\033[0m")
            print(f"\033[38;5;208mLesson: {workflow_message.lesson}\033[0m")

            # return the job to the leader, and let the leader decompose the job
            # workflow experience -> agent lesson
            lesson = "The job is too complicated to be executed by the expert"

            # (4.1) save the expert message in the database
            expert_message = self.save_output_agent_message(
                job=job, workflow_message=workflow_message, lesson=lesson
            )

            return expert_message
        raise Exception("The workflow status is not defined.")
