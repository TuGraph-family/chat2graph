from typing import Any, Dict, List, Tuple

from app.core.common.type import JobStatus
from app.core.model.message import ChatMessage, TextMessage
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

    def chat(self, chat_message: ChatMessage) -> Tuple[Dict[str, Any], str]:
        """Create user message and system message return the response data."""
        # create user message
        chat_message.set_assigned_expert_name("Question Answering Expert")  # TODO: to be removed
        self._message_service.save_message(message=chat_message)

        # make the chat message to the mulit-agent system
        session_wrapper = self._agentic_service.session(session_id=chat_message.get_session_id())
        # TODO: refactor the chat message to a more generic message
        job_wrapper = session_wrapper.submit(message=chat_message)

        # create system message
        system_chat_message = TextMessage(
            session_id=chat_message.get_session_id(),
            job_id=job_wrapper.id,
            role="system",
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
            agent_messages = self._message_service.get_agent_messages_by_job_id(job=job)

            # prepare the data using MessageView
            for msg in agent_messages:
                data.append(self._message_view.serialize_message(message=msg))

        return data, "Agent messages fetched successfully"

    def get_text_message(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Get message details by ID.

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
            return {"status": job_result.status.value.lower()}, "Job failed"

        if job_result.status in [JobStatus.CREATED, JobStatus.RUNNING]:
            print(f"Job still in progress for job_id: {job_id}")
            return {"status": job_result.status.value.lower()}, "Job still in progress"

        # update the message with the job result
        new_message = self._message_service.update_text_message(
            id=id, payload=job_result.result.get_payload()
        )

        # use MessageView to serialize the message
        data = self._message_view.serialize_message(new_message)
        # Add job status to the response
        data["status"] = job_result.status.value.lower()

        return data, "Message fetched successfully"

    def filter_text_messages_by_session(self, session_id: str) -> Tuple[List[Dict], str]:
        """Filter messages by session ID.

        Args:
            session_id (str): ID of the session

        Returns:
            Tuple[List[Dict], str]: A tuple containing a list of filtered message details and
                success message
        """
        text_messages: List[TextMessage] = self._message_service.filter_text_messages_by_session(
            session_id=session_id
        )

        # use MessageView to serialize all messages
        message_list = self._message_view.serialize_messages(text_messages)

        return message_list, f"Messages filtered by session ID {session_id} successfully"
