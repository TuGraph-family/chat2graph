from typing import Any, Dict, List, Optional

from app.core.common.singleton import Singleton
from app.core.dal.dao.message_dao import MessageDao
from app.core.dal.do.message_do import TextMessageDo
from app.core.model.job import Job, SubJob
from app.core.model.message import AgentMessage, Message, MessageType, TextMessage


class MessageService(metaclass=Singleton):
    """ChatMessage service"""

    def __init__(self):
        self._message_dao: MessageDao = MessageDao.instance

    def save_message(self, message: Message) -> Message:
        """Save a new message."""
        # create the message
        self._message_dao.save_message(message=message)
        return message

    def get_message(self, id: str, type: MessageType) -> Message:
        """Get a message by ID."""
        # fetch the message
        result = self._message_dao.get_by_id(id=id)
        if not result or str(result.type) != type.value:
            raise ValueError(f"Message with ID {id} not found or type mismatch")
        if type == MessageType.TEXT_MESSAGE:
            return TextMessage(
                id=str(result.id),
                session_id=str(result.session_id),
                job_id=str(result.job_id),
                role=str(result.role),
                payload=str(result.payload),
                timestamp=int(result.timestamp),
            )
        if type == MessageType.AGENT_MESSAGE:
            return AgentMessage(
                id=str(result.id),
                job_id=str(result.job_id),
                payload=str(result.payload),
                workflow_messages=[
                    self._message_dao.get_workflow_message(wf_id)
                    for wf_id in list(result.related_message_ids or [])
                ],
                timestamp=int(result.timestamp),
            )
        if type == MessageType.WORKFLOW_MESSAGE:
            return self._message_dao.get_workflow_message(id=str(result.id))
        # TODO: handle other message types

        raise ValueError(f"Unsupported message type: {type}")

    def get_message_by_job_id(self, job_id: str, type: MessageType) -> List[Message]:
        """Get all messages by job ID."""
        # fetch messages by job ID
        results = self._message_dao.filter_by(job_id=job_id)
        if not results:
            raise ValueError(f"No messages found for job ID {job_id}")
        if type == MessageType.TEXT_MESSAGE:
            return [
                TextMessage(
                    id=str(result.id),
                    session_id=str(result.session_id),
                    job_id=str(result.job_id),
                    role=str(result.role),
                    payload=str(result.payload),
                    timestamp=int(result.timestamp),
                )
                for result in results
                if str(result.type) == MessageType.TEXT_MESSAGE.value
            ]
        if type == MessageType.AGENT_MESSAGE:
            return [
                AgentMessage(
                    id=str(result.id),
                    job_id=str(result.job_id),
                    payload=str(result.payload),
                    workflow_messages=[
                        self._message_dao.get_workflow_message(wf_id)
                        for wf_id in list(result.related_message_ids or [])
                    ],
                    timestamp=int(result.timestamp),
                )
                for result in results
                if str(result.type) == MessageType.AGENT_MESSAGE.value
            ]
        # TODO: handle other message types

        raise ValueError(f"Unsupported message type: {type}")

    def get_by_type(self, type: MessageType) -> List[Message]:
        """Get all messages by type."""
        # fetch messages by type
        results = self._message_dao.get_by_type(type=type)
        if type == MessageType.TEXT_MESSAGE:
            return [
                TextMessage(
                    id=str(result.id),
                    session_id=str(result.session_id),
                    job_id=str(result.job_id),
                    role=str(result.role),
                    payload=str(result.payload),
                    timestamp=int(result.timestamp),
                )
                for result in results
            ]
        if type == MessageType.AGENT_MESSAGE:
            return [
                AgentMessage(
                    id=str(result.id),
                    job_id=str(result.job_id),
                    payload=str(result.payload),
                    workflow_messages=[
                        self._message_dao.get_workflow_message(wf_id)
                        for wf_id in list(result.related_message_ids or [])
                    ],
                    timestamp=int(result.timestamp),
                )
                for result in results
            ]
        if type == MessageType.WORKFLOW_MESSAGE:
            return [self._message_dao.get_workflow_message(id=str(result.id)) for result in results]
        # TODO: handle other message types

        raise ValueError(f"Unsupported message type: {type}")

    def get_agent_message_by_job(self, job: SubJob) -> AgentMessage:
        """Get agent messages by job ID."""
        return self._message_dao.get_agent_message_by_job(job=job)

    def get_text_message_by_job_and_role(self, job: Job, role: str) -> TextMessage:
        """Get system text messages by job ID."""
        return self._message_dao.get_text_message_by_job_and_role(job=job, role=role)

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
    ) -> TextMessage:
        """Update a message by ID.

        Args:
            id (str): ID of the message
            job_id (Optional[str]): Updated job ID
            role (Optional[str]): Updated role
            payload (Optional[str]): Updated content of the message

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
            )

        return TextMessage(
            id=str(existing_message.id),
            session_id=str(existing_message.session_id),
            job_id=str(existing_message.job_id),
            role=str(existing_message.role),
            payload=str(existing_message.payload),
            timestamp=int(existing_message.timestamp),
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
            )
            for result in results
        ]
