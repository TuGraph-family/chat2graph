from typing import Dict, List, Optional

from app.core.common.singleton import Singleton
from app.core.dal.dao import MessageDAO
from app.core.dal.database import DB
from app.core.model.message import ChatMessage
from app.server.common.util import ServiceException


class MessageService(metaclass=Singleton):
    """ChatMessage service"""

    def __init__(self):
        self._messages: Dict[str, ChatMessage] = {}
        self._dao = MessageDAO(DB())

    def create_message(
        self,
        session_id: str,
        message_type: str,
        role: str,
        message: str,
        job_id: Optional[str] = None,
        others: Optional[str] = None,
    ) -> ChatMessage:
        """Create a new message.

        Args:
            session_id (str): ID of the associated session
            message_type (str): Type of the message
            role (str): Role of the sender
            message (str): Content of the message
            job_id (Optional[str]): Job ID related to the message.
            others (Optional[str]): Additional information.

        Returns:
            ChatMessage: ChatMessage object
        """
        # create the message
        result = self._dao.create(
            session_id=session_id,
            message_type=message_type,
            job_id=job_id,
            role=role,
            message=message,
            others=others,
        )
        return ChatMessage(
            id=result.id,
            session_id=result.session_id,
            message_type=result.message_type,
            job_id=result.job_id,
            role=result.role,
            payload=result.message,
            timestamp=result.timestamp,
            others=result.others,
        )

    def get_message(self, id: str) -> ChatMessage:
        """Get a message by ID."""
        # fetch the message
        result = self._dao.get_by_id(id=id)
        if not result:
            raise ServiceException(f"ChatMessage with ID {id} not found")
        return ChatMessage(
            id=result.id,
            session_id=result.session_id,
            message_type=result.message_type,
            job_id=result.job_id,
            role=result.role,
            payload=result.message,
            timestamp=result.timestamp,
            others=result.others,
        )

    def delete_message(self, id: str):
        """Delete a message by ID."""
        # delete the message
        message = self._dao.get_by_id(id=id)
        if not message:
            raise ServiceException(f"ChatMessage with ID {id} not found")
        self._dao.delete(id=id)

    def update_message(
        self,
        id: str,
        message_type: Optional[str] = None,
        job_id: Optional[str] = None,
        role: Optional[str] = None,
        message: Optional[str] = None,
        others: Optional[str] = None,
    ) -> ChatMessage:
        """Update a message by ID.

        Args:
            id (str): ID of the message
            message_type (Optional[str]): Updated type of the message
            job_id (Optional[str]): Updated job ID
            role (Optional[str]): Updated role
            message (Optional[str]): Updated content of the message
            others (Optional[str]): Updated additional information

        Returns:
            ChatMessage: Updated ChatMessage object
        """
        # fetch the existing message
        existing_message = self._dao.get_by_id(id=id)
        if not existing_message:
            raise ServiceException(f"ChatMessage with ID {id} not found")

        # prepare update fields
        update_fields = {}
        if message_type is not None and message_type != existing_message.message_type:
            update_fields["message_type"] = message_type
        if job_id is not None and job_id != existing_message.job_id:
            update_fields["job_id"] = job_id
        if role is not None and role != existing_message.role:
            update_fields["role"] = role
        if message is not None and message != existing_message.message:
            update_fields["message"] = message
        if others is not None and others != existing_message.others:
            update_fields["others"] = others

        # update only if there are changes
        if update_fields:
            updated_message = self._dao.update(id=id, **update_fields)
            return ChatMessage(
                id=updated_message.id,
                session_id=updated_message.session_id,
                message_type=updated_message.message_type,
                job_id=updated_message.job_id,
                role=updated_message.role,
                payload=updated_message.message,
                timestamp=updated_message.timestamp,
                others=updated_message.others,
            )
        return ChatMessage(
            id=existing_message.id,
            session_id=existing_message.session_id,
            message_type=existing_message.message_type,
            job_id=existing_message.job_id,
            role=existing_message.role,
            payload=existing_message.message,
            timestamp=existing_message.timestamp,
            others=existing_message.others,
        )

    def get_all_messages(self) -> List[ChatMessage]:
        """Get all messages."""

        results = self._dao.get_all()
        return [
            ChatMessage(
                id=result.id,
                session_id=result.session_id,
                message_type=result.message_type,
                job_id=result.job_id,
                role=result.role,
                payload=result.message,
                timestamp=result.timestamp,
                others=result.others,
            )
            for result in results
        ]

    def filter_messages_by_session(self, session_id: str) -> List[ChatMessage]:
        """Filter messages by session ID.

        Args:
            session_id (str): ID of the session

        Returns:
            List[ChatMessage]: List of ChatMessage objects
        """
        # fetch filtered messages
        results = self._dao.filter_by(session_id=session_id)
        return [
            ChatMessage(
                id=result.id,
                session_id=result.session_id,
                message_type=result.message_type,
                job_id=result.job_id,
                role=result.role,
                payload=result.message,
                timestamp=result.timestamp,
                others=result.others,
            )
            for result in results
        ]
