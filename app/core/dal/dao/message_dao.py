from typing import Any, Dict, List, Optional, cast

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.common.type import ChatMessageRole
from app.core.dal.dao.dao import Dao
from app.core.dal.do.message_do import (
    AgentMessageDo,
    FileMessageDo,
    HybridMessageDo,
    MessageDo,
    ModelMessageAO,
    TextMessageDo,
    WorkflowMessageDo,
)
from app.core.model.job import Job, SubJob
from app.core.model.message import (
    AgentMessage,
    FileMessage,
    HybridMessage,
    Message,
    MessageType,
    ModelMessage,
    TextMessage,
    WorkflowMessage,
)


class MessageDao(Dao[MessageDo]):
    """Message dao"""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(MessageDo, session)

    def save_message(self, message: Message) -> MessageDo:
        """Create a new message."""
        message_do = self.__save_message(message)
        message_dict = {c.name: getattr(message_do, c.name) for c in message_do.__table__.columns}
        try:
            self.create(**message_dict)
        except Exception:
            message_dict.pop("id", None)
            self.update(id=str(message_do.id), **message_dict)
        return message_do

    def __save_message(self, message: Message) -> MessageDo:
        """Create a message model instance."""

        if isinstance(message, WorkflowMessage):
            return WorkflowMessageDo(
                type=MessageType.WORKFLOW_MESSAGE.value,
                payload=WorkflowMessage.serialize_payload(message.get_payload()),
                id=message.get_id(),
                job_id=message.get_id(),
                timestamp=message.get_timestamp(),
            )

        if isinstance(message, AgentMessage):
            related_message_ids: List[str] = [wf.get_id() for wf in message.get_workflow_messages()]
            return AgentMessageDo(
                type=MessageType.AGENT_MESSAGE.value,
                payload=message.get_payload(),
                lesson=message.get_lesson(),
                related_message_ids=related_message_ids,
                id=message.get_id(),
                job_id=message.get_job_id(),
                timestamp=message.get_timestamp(),
            )

        if isinstance(message, ModelMessage):
            # TODO: to refine the fields for model message
            # source_type: MessageSourceType = MessageSourceType.MODEL, # TODO
            # function_calls: Optional[List[FunctionCallResult]] = None,# TODO

            return ModelMessageAO(
                type=MessageType.MODEL_MESSAGE.value,
                payload=message.get_payload(),
                id=message.get_id(),
                job_id=message.get_job_id(),
                timestamp=message.get_timestamp(),
                step=message.get_step(),
            )

        if isinstance(message, TextMessage):
            return TextMessageDo(
                type=MessageType.TEXT_MESSAGE.value,
                payload=message.get_payload(),
                timestamp=message.get_timestamp(),
                role=message.get_role().value,
                assigned_expert_name=message.get_assigned_expert_name(),
                id=message.get_id(),
                session_id=message.get_session_id(),
                job_id=message.get_job_id(),
            )
        if isinstance(message, FileMessage):
            return FileMessageDo(
                type=MessageType.FILE_MESSAGE.value,
                id=message.get_id(),
                job_id=message.get_job_id(),
                session_id=message.get_session_id(),
                related_message_ids=[message.get_file_id()],
                timestamp=message.get_timestamp(),
            )
        if isinstance(message, HybridMessage):
            return HybridMessageDo(
                type=MessageType.HYBRID_MESSAGE.value,
                id=message.get_id(),
                session_id=message.get_session_id(),
                job_id=message.get_job_id(),
                related_message_ids=[msg.get_id() for msg in message.get_attached_messages()],
                timestamp=message.get_timestamp(),
            )
        raise ValueError(f"Unsupported message type: {type(message)}")

    def get_by_type(self, type: MessageType) -> List[MessageDo]:
        """get messages by type"""
        return self.session.query(self._model).filter(self._model.type == type.value).all()

    def get_workflow_message(self, id: str) -> WorkflowMessage:
        """Get a message by ID."""
        # fetch the message
        result = self.get_by_id(id=id)
        if not result:
            raise ValueError(f"Workflow message with ID {id} not found")
        payload: Dict[str, Any] = WorkflowMessage.deserialize_payload(str(result.payload))
        return WorkflowMessage(
            id=str(result.id),
            payload=payload,
            job_id=str(result.job_id),
            timestamp=int(result.timestamp),
        )

    def get_agent_message_by_job(self, job: SubJob) -> AgentMessage:
        """Get agent messages by job."""
        results: List[AgentMessageDo] = (
            self.session.query(self._model)
            .filter(
                self._model.type == MessageType.AGENT_MESSAGE.value,
                self._model.job_id == job.id,
            )
            .all()
        )

        assert len(results) == 1, f"Job {job.id} has multiple or not agent messages."

        result = results[0]
        return AgentMessage(
            id=str(result.id),
            job_id=job.id,
            payload=str(result.payload),
            workflow_messages=[
                self.get_workflow_message(wf_id) for wf_id in list(result.related_message_ids or [])
            ],
            timestamp=int(result.timestamp),
        )

    def get_text_message_by_job_and_role(self, job: Job, role: ChatMessageRole) -> TextMessage:
        """Get system text messages by job and role."""
        results: List[TextMessageDo] = (
            self.session.query(self._model)
            .filter(
                self._model.type == MessageType.TEXT_MESSAGE.value,
                self._model.job_id == job.id,
                self._model.role == role.value,
            )
            .all()
        )

        assert len(results) == 1, f"Job {job.id} has multiple or not text messages by system."

        result = results[0]
        return TextMessage(
            id=cast(str, result.id),
            session_id=cast(Optional[str], result.session_id),
            job_id=cast(str, job.id),
            role=ChatMessageRole(str(result.role)),
            payload=cast(str, result.payload),
            timestamp=int(result.timestamp),
            assigned_expert_name=cast(Optional[str], result.assigned_expert_name),
        )
