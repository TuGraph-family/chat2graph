from typing import Any, Dict, List, Optional, Tuple

from app.core.common.type import ChatMessageType, JobStatus
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

    def chat(
        self,
        session_id: str,
        payload: str,
        chat_message_type: ChatMessageType = ChatMessageType.TEXT,
        others: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Create user message and system message return the response data.

        Args:
            session_id (str): ID of the associated session
            payload (str): Content of the message
            chat_message_type (ChatMessageType): Type of the message.
                Defaults to ChatMessageType.TEXT.
            others (Optional[str]): Additional information. Defaults to None.

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing message details and success message.
        """
        # create user message
        text_message = TextMessage(
            session_id=session_id,
            chat_message_type=chat_message_type,
            role="user",
            payload=payload,
            others=others,
            assigned_expert_name="Question Answering Expert",  # TODO: to be removed
        )
        self._message_service.save_message(message=text_message)

        # make the chat message to the mulit-agent system
        session_wrapper = self._agentic_service.session(session_id=session_id)
        # TODO: refactor the chat message to a more generic message
        job_wrapper = session_wrapper.submit(message=text_message)

        # create system message
        system_chat_message = TextMessage(
            session_id=session_id,
            chat_message_type=ChatMessageType.TEXT,
            job_id=job_wrapper.id,
            role="system",
            payload="",  # TODO: to be handled
            others=others,
        )
        self._message_service.save_message(message=system_chat_message)

        # Use MessageView to serialize the message for API response
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
        assert job_id, "Job ID is not defined in the message"
        job_result = self._job_service.query_job_result(job_id=job_id)

        # check the job status
        if job_result.status == JobStatus.FAILED:
            print(f"Job failed for job_id: {job_id}")
            return {"status": job_result.status.value}, "Job failed"

        if job_result.status in [JobStatus.CREATED, JobStatus.RUNNING]:
            print(f"Job still in progress for job_id: {job_id}")
            return {"status": job_result.status.value}, "Job still in progress"

        # update the message with the job result
        new_message = self._message_service.update_text_message(
            id=id, payload=job_result.result.get_payload()
        )

        # Use MessageView to serialize the message
        data = self._message_view.serialize_message(new_message)
        # Add job status to the response
        data["status"] = job_result.status.value

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

        # Use MessageView to serialize all messages
        message_list = self._message_view.serialize_messages(text_messages)

        return message_list, f"Messages filtered by session ID {session_id} successfully"
