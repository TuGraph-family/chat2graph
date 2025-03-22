from typing import List, cast

from app.core.common.singleton import Singleton
from app.core.common.type import ChatMessageRole
from app.core.dal.dao.message_dao import MessageDao
from app.core.dal.do.message_do import TextMessageDo
from app.core.model.message import Message, MessageType, TextMessage


class MessageService(metaclass=Singleton):
    """ChatMessage service"""

    def __init__(self):
        self._message_dao: MessageDao = MessageDao.instance

    def save_message(self, message: Message) -> Message:
        """Save a new message."""
        # create the message
        self._message_dao.save_message(message=message)
        return message

    def get_message_by_job_id(self, job_id: str, message_type: MessageType) -> List[Message]:
        """Get all messages by job ID."""
        # fetch messages by job ID
        results = self._message_dao.filter_by(job_id=job_id, type=message_type.value)
        if not results:
            return []
        return [self._message_dao.parse_into_message(message_do=result) for result in results]

    def get_text_message_by_job_id_and_role(
        self, job_id: str, role: ChatMessageRole
    ) -> TextMessage:
        """Get system text messages by job ID."""
        results: List[TextMessageDo] = self._message_dao.get_text_message_by_job_id_and_role(
            job_id=job_id, role=role
        )
        assert len(results) == 1, f"Job {job_id} has multiple or not text messages by system."

        result = results[0]
        return cast(TextMessage, self._message_dao.parse_into_message(message_do=result))

    def filter_text_messages_by_session(self, session_id: str) -> List[TextMessage]:
        """Filter messages by session ID.

        Args:
            session_id (str): ID of the session

        Returns:
            List[TextMessage]: List of TextMessage objects
        """
        # fetch filtered messages
        results = self._message_dao.filter_by(session_id=session_id)
        return [
            cast(TextMessage, self._message_dao.parse_into_message(message_do=result))
            for result in results
        ]
