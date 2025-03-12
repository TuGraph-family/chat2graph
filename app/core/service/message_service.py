from typing import Any, Dict, List, Optional

from app.core.common.singleton import Singleton
from app.core.dal.dao.message_dao import MessageDao
from app.core.dal.do.message_do import TextMessageDo
from app.core.model.job import Job
from app.core.model.message import AgentMessage, Message, MessageType, TextMessage


class MessageService(metaclass=Singleton):
    """ChatMessage service"""

    def __init__(self):
        self._message_dao: MessageDao = MessageDao.instance

    def save_message(self, message: Message) -> Message:
        """Save a new message."""
        # create the message
        self._message_dao.save_message_do(message=message)
        return message

    def get_agent_messages_by_job_id(self, job: Job) -> List[AgentMessage]:
        """Get agent messages by job ID."""
        # fetch agent messages
        return self._message_dao.get_agent_messages_by_job(job=job)

    def get_text_message(self, id: str) -> TextMessage:
        """Get a message by ID."""
        # fetch the message
        result = self._message_dao.get_by_id(id=id)
        if not result:
            raise ValueError(f"TextMessage with ID {id} not found")
        return TextMessage(
            id=str(result.id),
            session_id=str(result.session_id),
            job_id=str(result.job_id),
            role=str(result.role),
            payload=str(result.payload),
            timestamp=int(result.timestamp),
            others=str(result.others),
        )

    def delete_text_message(self, id: str) -> None:
        """Delete a message by ID."""
        # delete the message
        message = self._message_dao.get_by_id(id=id)
        if not message:
            raise ValueError(f"TexttMessage with ID {id} not found")
        self._message_dao.delete(id=id)

    def update_text_message(
        self,
        id: str,
        job_id: Optional[str] = None,
        role: Optional[str] = None,
        payload: Optional[str] = None,
        others: Optional[str] = None,
    ) -> TextMessage:
        """Update a message by ID.

        Args:
            id (str): ID of the message
            job_id (Optional[str]): Updated job ID
            role (Optional[str]): Updated role
            payload (Optional[str]): Updated content of the message
            others (Optional[str]): Updated additional information

        Returns:
            TextMessage: Updated TextMessage object
        """
        # fetch the existing message
        existing_message: Optional[TextMessageDo] = self._message_dao.get_by_id(id=id)
        if not existing_message:
            raise ValueError(f"TextMessage with ID {id} not found")

        # prepare update fields
        update_fields: Dict[str, Any] = {}
        if job_id is not None and job_id != str(existing_message.job_id):
            update_fields["job_id"] = job_id
        if role is not None and role != str(existing_message.role):
            update_fields["role"] = role
        if payload is not None and payload != str(existing_message.payload):
            update_fields["payload"] = payload
        if others is not None and others != str(existing_message.others):
            update_fields["others"] = others

        # update only if there are changes
        if update_fields:
            updated_message: TextMessageDo = self._message_dao.update(id=id, **update_fields)
            return TextMessage(
                id=str(updated_message.id),
                session_id=str(updated_message.session_id),
                job_id=str(updated_message.job_id),
                role=str(updated_message.role),
                payload=str(updated_message.payload),
                timestamp=int(updated_message.timestamp),
                others=str(updated_message.others),
            )

        return TextMessage(
            id=str(existing_message.id),
            session_id=str(existing_message.session_id),
            job_id=str(existing_message.job_id),
            role=str(existing_message.role),
            payload=str(existing_message.payload),
            timestamp=int(existing_message.timestamp),
            others=str(existing_message.others),
        )

    def get_all_text_messages(self) -> List[TextMessage]:
        """Get all messages."""

        results = self._message_dao.get_by_type(type=MessageType.TEXT_MESSAGE)
        return [
            TextMessage(
                id=str(result.id),
                session_id=str(result.session_id),
                job_id=str(result.job_id),
                role=str(result.role),
                payload=str(result.payload),
                timestamp=int(result.timestamp),
                others=str(result.others),
            )
            for result in results
        ]

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
            TextMessage(
                id=str(result.id),
                session_id=str(result.session_id),
                job_id=str(result.job_id),
                role=str(result.role),
                payload=str(result.payload),
                timestamp=int(result.timestamp),
                others=str(result.others),
            )
            for result in results
        ]
