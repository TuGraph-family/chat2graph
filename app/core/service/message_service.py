from typing import Any, Dict, List, Optional

from app.core.common.singleton import Singleton
from app.core.common.type import ChatMessageType
from app.core.dal.dao.message_dao import MessageDao
from app.core.dal.do.message_do import MessageType, TextMessageDo
from app.core.model.job import Job
from app.core.model.message import AgentMessage, TextMessage, WorkflowMessage


class MessageService(metaclass=Singleton):
    """ChatMessage service"""

    def __init__(self):
        self._message_dao: MessageDao = MessageDao.instance

    def save_workflow_message(self, message: WorkflowMessage, job_id: str) -> WorkflowMessage:
        """Save a new workflow message."""
        self._message_dao.create_message_do(message=message, job_id=job_id)
        return message

    def save_agent_message(self, message: AgentMessage) -> AgentMessage:
        """Save a new agent message.

        Note that it dose not save the job of the agent message in the database.
        And it dose not either save the workflow messages of the agent message in the database.
        """
        self._message_dao.create_message_do(message=message)
        return message

    def save_text_message(self, message: TextMessage) -> TextMessage:
        """Save a new text message."""
        # create the message
        self._message_dao.create_message_do(message=message)
        return message

    def get_agent_messages_by_job_id(self, job: Job) -> List[AgentMessage]:
        """Get agent messages by job ID."""
        # fetch agent messages
        return self._message_dao.get_agent_messages_by_job(job=job)

    def get_text_message(self, id: str) -> TextMessage:
        """Get a message by ID."""
        # fetch the message
        result = self._message_dao.get_by_id(id=id)
        for do in self._message_dao.get_all():
            print(
                f"[DEBUG] id: {do.id}, type: {do.type}, payload: {str(do.payload)}, job_id: {do.job_id}, role: {do.role}"
            )
        if not result:
            raise ValueError(f"TextMessage with ID {id} not found")
        return TextMessage(
            id=str(result.id),
            session_id=str(result.session_id),
            chat_message_type=ChatMessageType(str(result.chat_message_type)),
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
        chat_message_type: ChatMessageType = ChatMessageType.TEXT,
        job_id: Optional[str] = None,
        role: Optional[str] = None,
        payload: Optional[str] = None,
        others: Optional[str] = None,
    ) -> TextMessage:
        """Update a message by ID.

        Args:
            id (str): ID of the message
            chat_message_type (Optional[str]): Updated type of the message
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
        if chat_message_type.value != str(existing_message.chat_message_type):
            update_fields["chat_message_type"] = chat_message_type
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
                chat_message_type=ChatMessageType(str(updated_message.chat_message_type)),
                job_id=str(updated_message.job_id),
                role=str(updated_message.role),
                payload=str(updated_message.payload),
                timestamp=int(updated_message.timestamp),
                others=str(updated_message.others),
            )

        return TextMessage(
            id=str(existing_message.id),
            session_id=str(existing_message.session_id),
            chat_message_type=ChatMessageType(str(existing_message.chat_message_type)),
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
                chat_message_type=ChatMessageType(str(result.chat_message_type)),
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
                chat_message_type=ChatMessageType(str(result.chat_message_type)),
                job_id=str(result.job_id),
                role=str(result.role),
                payload=str(result.payload),
                timestamp=int(result.timestamp),
                others=str(result.others),
            )
            for result in results
        ]
