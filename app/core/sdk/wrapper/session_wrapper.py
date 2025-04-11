from typing import List, Optional, cast

from app.core.common.async_func import run_in_thread
from app.core.model.job import Job
from app.core.model.message import ChatMessage, HybridMessage, TextMessage
from app.core.model.session import Session
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.service.session_service import SessionService
from app.server.manager.view.message_view import MessageView


class SessionWrapper:
    """Facade for managing sessions."""

    def __init__(self, session: Optional[Session] = None):
        session_service: SessionService = SessionService.instance
        self._session: Session = session or session_service.get_session()

    @property
    def session(self) -> Session:
        """Get the session."""
        return self._session

    def submit(self, message: ChatMessage) -> JobWrapper:
        """Submit the job."""
        message_service: MessageService = MessageService.instance
        job_service: JobService = JobService.instance

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
        session_id: str = self._session.id

        # get all job ids in the session
        original_jobs = job_service.get_original_jobs_by_session_id(session_id=session_id)
        original_job_ids = [j.id for j in original_jobs]

        # get message view data for the job
        conversation_views_history: List[MessageView] = []
        for original_job_id in original_job_ids:
            conversation_view = job_service.get_conversation_view(original_job_id=original_job_id)
            conversation_views_history.append(conversation_view)

        historical_context = self._format_conversation_history(
            conversation_views=conversation_views_history, current_question_message=text_message
        )

        # (3) create and save the job
        job = Job(
            goal=text_message.get_payload(),
            context=historical_context,
            session_id=self._session.id,
            assigned_expert_name=text_message.get_assigned_expert_name(),
        )
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

    def _format_conversation_history(
        self, conversation_views: List[MessageView], current_question_message: Optional[TextMessage]
    ) -> str:
        """Converts a list of MessageView objects into a single, LLM-friendly string.

        This format clearly delineates conversation turns, user questions,
        agent's intermediate thinking steps, and the agent's final answers.

        Args:
            conversation_views (List[MessageView]): A list of MessageView objects representing
                the conversation history.
            current_question_message (Optional[TextMessage]): The current user question message.

        Returns:
            str: A formatted string representing the entire conversation history.
        """
        if len(conversation_views) == 0:
            return ""

        message_views = [
            "---- Conversation History of the Given Task ----",
            "Please select the useful information from the history to assist in accurately "
            "interpreting the user's intent and decomposing the task appropriately.",
        ]
        for view in conversation_views:
            # 1. user question
            message_views.append("[User Message]")
            message_views.append(cast(str, view.question.get_payload()).strip())

            # 2. agent thinking steps (if available)
            if view.thinking_messages:
                message_views.append("[AI Thinking Chain]")
                for j, thinking_msg in enumerate(view.thinking_messages):
                    # Add numbering for clarity within the thinking process
                    message_views.append(f"Step {j + 1}:")
                    thinking_msg_payload = thinking_msg.get_payload() or "(No message)"
                    message_views.append(thinking_msg_payload.strip())

            # 3. ai answer
            message_views.append("[AI Message]")
            message_views.append(cast(str, view.answer.get_payload()).strip())

        if current_question_message:
            message_views.append("[User Message]")
            message_views.append(cast(str, current_question_message.get_payload()).strip())

        message_views.append("---- End of Conversation History ----")

        return "\n".join(message_views)
