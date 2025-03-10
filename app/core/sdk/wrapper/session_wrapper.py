from typing import List, Optional

from app.core.common.async_func import run_in_thread
from app.core.model.job import Job
from app.core.model.message import ChatMessage, TextMessage
from app.core.model.session import Session
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.service.message_service import MessageService
from app.core.service.session_service import SessionService


class SessionWrapper:
    """Facade for managing sessions."""

    def __init__(self, session: Optional[Session] = None):
        session_service: SessionService = SessionService.instance
        self._session: Session = session or session_service.get_session()

    def submit(self, message: ChatMessage) -> JobWrapper:
        """Submit the job."""
        # get chat history (text messages), and it will be used as the context of the job
        session_id: Optional[str] = message.get_session_id()
        if session_id:
            message_service: MessageService = MessageService.instance
            history_text_messages: List[TextMessage] = (
                message_service.filter_text_messages_by_session(session_id=session_id)
            )
        else:
            history_text_messages = []

        job = Job(
            goal=message.get_payload(),
            context="Chat history of the job goal:\n"
            + "\n".join(
                [
                    f"[{message.get_role()}]: {message.get_payload()}"
                    for message in history_text_messages
                ]
            ),
            session_id=self._session.id,
            assigned_expert_name=message.get_assigned_expert_name(),
        )
        job_wrapper = JobWrapper(job)

        run_in_thread(job_wrapper.execute)

        return job_wrapper
