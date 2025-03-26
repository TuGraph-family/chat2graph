from typing import List, Optional, cast

from app.core.common.async_func import run_in_thread
from app.core.model.job import Job
from app.core.model.message import ChatMessage, HybridMessage, TextMessage
from app.core.model.session import Session
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.service.session_service import SessionService


class SessionWrapper:
    """Facade for managing sessions."""

    def __init__(self, session: Optional[Session] = None):
        session_service: SessionService = SessionService.instance
        self._session: Session = session or session_service.get_session()

    def submit(self, message: ChatMessage) -> JobWrapper:
        """Submit the job."""
        message_service: MessageService = MessageService.instance

        # (1) get text message from the hybrid message
        if isinstance(message, HybridMessage):
            # save the attached messages
            attached_messages = message.get_attached_messages()
            for attached_message in attached_messages:
                message_service.save_message(message=attached_message)

            # get the instruction message in the hybrid message
            text_message: TextMessage = cast(TextMessage, message.get_instruction_message())
        elif isinstance(message, TextMessage):
            text_message = message
        else:
            raise ValueError(
                f"Unsupported message type {type(message)} to submit to the multi-agent system"
            )

        # (2) get chat history (text messages), and it will be used as the context of the job
        session_id: Optional[str] = message.get_session_id()
        if session_id:
            history_text_messages: List[TextMessage] = (
                message_service.filter_text_messages_by_session(session_id=session_id)
            )
            if len(history_text_messages) > 0:
                historical_context = "Chat history of the job goal:\n" + "\n".join(
                    [
                        f"[Chat history: {msg.get_role().value}] said: {msg.get_payload()}"
                        for msg in history_text_messages
                    ]
                )
            else:
                historical_context = ""
        else:
            historical_context = ""

        # (3) create and save the job
        job = Job(
            goal=text_message.get_payload(),
            context=historical_context,
            session_id=self._session.id,
            assigned_expert_name=text_message.get_assigned_expert_name(),
        )
        job_service: JobService = JobService.instance
        job_service.save_job(job=job)
        job_wrapper = JobWrapper(job)

        # (4) update the text message with the job ID
        if isinstance(message, HybridMessage):
            message.set_job_id(job_wrapper.id)
            message_service.save_message(message=message)
        text_message.set_job_id(job_wrapper.id)
        message_service.save_message(message=text_message)

        # (5) update the latest job id in the session
        session_service: SessionService = SessionService.instance
        self._session.latest_job_id = job_wrapper.id
        session_service.update_session(session=self._session)

        # (6) execute the job
        run_in_thread(job_wrapper.execute)

        return job_wrapper
