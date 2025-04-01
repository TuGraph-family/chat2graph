from typing import Any, Dict, Tuple

from app.core.common.type import ChatMessageRole
from app.core.model.message import ChatMessage, HybridMessage, TextMessage
from app.core.sdk.agentic_service import AgenticService
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.service.session_service import SessionService
from app.server.manager.view.message_view import MessageViewTransformer


class MessageManager:
    """Message Manager class to handle business logic"""

    def __init__(self):
        self._agentic_service: AgenticService = AgenticService.instance
        self._session_service: SessionService = SessionService.instance
        self._message_service: MessageService = MessageService.instance
        self._job_service: JobService = JobService.instance
        self._agent_service: AgentService = AgentService.instance
        self._message_view: MessageViewTransformer = MessageViewTransformer()

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

        # update the name of the session
        if isinstance(chat_message, TextMessage):
            session_wrapper.session.name = chat_message.get_payload()
        if isinstance(chat_message, HybridMessage):
            session_wrapper.session.name = chat_message.get_instruction_message().get_payload()
        self._session_service.save_session(session=session_wrapper.session)

        # use MessageView to serialize the message for API response
        system_data = self._message_view.serialize_message(system_chat_message)
        return system_data, "Message created successfully"
