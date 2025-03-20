from typing import Any, Dict, List, Tuple

from app.core.common.type import ChatMessageRole
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
        # create the session wrapper
        session_wrapper = self._agentic_service.session(session_id=chat_message.get_session_id())

        # submit the message to the multi-agent system
        job_wrapper = session_wrapper.submit(message=chat_message)

        # create system message
        system_chat_message = TextMessage(
            session_id=chat_message.get_session_id(),
            job_id=job_wrapper.id,
            role=ChatMessageRole.SYSTEM,
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
            agent_message = self._message_service.get_agent_message_by_job(job=job)

            # prepare the data using MessageView
            data.append(self._message_view.serialize_message(message=agent_message))

        return data, "Agent messages fetched successfully"
