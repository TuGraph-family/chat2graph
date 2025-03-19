from typing import Any, Dict, List, Tuple

from app.core.common.type import JobStatus
from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.server.manager.view.message_view import MessageView


class MessageManager:
    """Message Manager class to handle business logic"""

    def __init__(self):
        self._agentic_service: AgenticService = AgenticService.instance
        self._message_service: MessageService = MessageService.instance
        self._job_service: JobService = JobService.instance
        self._agent_service: AgentService = AgentService.instance
        self._message_view: MessageView = MessageView()

    def chat(self, text_message: TextMessage) -> Tuple[Dict[str, Any], str]:
        """Create user message and system message return the response data."""
        # make the chat message to the mulit-agent system
        session_wrapper = self._agentic_service.session(session_id=text_message.get_session_id())
        # TODO: refactor the chat message to a more generic message
        job_wrapper = session_wrapper.submit(message=text_message)

        # create system message
        system_chat_message = TextMessage(
            session_id=text_message.get_session_id(),
            job_id=job_wrapper.id,
            role="SYSTEM",
            payload="",  # TODO: to be handled
        )
        self._message_service.save_message(message=system_chat_message)

        # use MessageView to serialize the message for API response
        system_data = self._message_view.serialize_message(system_chat_message)
        return system_data, "Message created successfully"

    def get_agent_messages_by_job(self, original_job_id: str) -> Tuple[List[Dict[str, Any]], str]:
        """Get agent messages by job.

        Args:
            job (Job): The job instance

        Returns:
            Tuple[List[Dict[str, Any]], str]: A tuple containing a list of agent message details and
                success message
        """
        jobs = self._job_service.get_subjobs(original_job_id=original_job_id)
        data: List[Dict[str, Any]] = []

        for job in jobs:
            # get the agent messages
            # TODO: it shold return one agent message for the job
            agent_message = self._message_service.get_agent_message_by_job(job=job)

            # prepare the data using MessageView
            data.append(self._message_view.serialize_message(message=agent_message))

        return data, "Agent messages fetched successfully"

    def query_text_message(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Query message details by ID.

        If the job result is available, it will return the job result in the message details.

        Args:
            id (str): ID of the message

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing message details and success message
        """
        # get the chat message
        chat_message = self._message_service.get_text_message(id=id)

        # query the job result
        job_id = chat_message.get_job_id()
        job_result = self._job_service.query_job_result(job_id=job_id)

        # check the job status
        if job_result.status == JobStatus.FAILED:
            print(f"Job failed for job_id: {job_id}")
            return {"status": job_result.status.value}, "Job failed"

        if job_result.status in [JobStatus.CREATED, JobStatus.RUNNING]:
            print(f"Job still in progress for job_id: {job_id}")
            return {"status": job_result.status.value}, "Job still in progress"

        # update the message with the job result
        # new_message = self._message_service.update_text_message(
        #     id=id, payload=job_result.message.get_payload()
        # )
        new_message = self._message_service.get_text_message_by_job_and_role(
            job=self._job_service.get_orignal_job(job_id), role="SYSTEM"
        )

        # use MessageView to serialize the message
        data = self._message_view.serialize_message(new_message)
        # Add job status to the response
        data["status"] = job_result.status.value

        return data, "Message fetched successfully"
