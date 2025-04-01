from typing import List, cast

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
        message_do = self.parse_into_message_do(message)
        message_dict = {c.name: getattr(message_do, c.name) for c in message_do.__table__.columns}
        try:
            self.create(**message_dict)
        except Exception:
            message_dict.pop("id", None)
            self.update(id=str(message_do.id), **message_dict)
        return message_do

    def get_message(self, id: str) -> Message:
        """Get a message by ID."""
        # fetch the message
        result = self.get_by_id(id=id)
        if not result:
            raise ValueError(f"Message with ID {id} not found")
        return self.parse_into_message(message_do=result)

    def get_text_message_by_job_id_and_role(
        self, job_id: str, role: ChatMessageRole
    ) -> List[TextMessageDo]:
        """Get text message by job and role."""
        return (
            self.session.query(self._model)
            .filter(
                self._model.type == MessageType.TEXT_MESSAGE.value,
                self._model.job_id == job_id,
                self._model.role == role.value,
            )
            .all()
        )

    def parse_into_message_do(self, message: Message) -> MessageDo:
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
            # source_type: MessageSourceType = MessageSourceType.MODEL,
            # function_calls: Optional[List[FunctionCallResult]] = None,

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

    def parse_into_message(self, message_do: MessageDo) -> Message:
        """Create a message model instance."""
        message_type = MessageType(str(message_do.type))

        if message_type == MessageType.WORKFLOW_MESSAGE:
            return WorkflowMessage(
                id=str(message_do.id),
                payload=WorkflowMessage.deserialize_payload(str(message_do.payload)),
                job_id=str(message_do.job_id),
                timestamp=int(message_do.timestamp),
            )
        if message_type == MessageType.AGENT_MESSAGE:
            return AgentMessage(
                id=str(message_do.id),
                job_id=str(message_do.job_id),
                payload=str(message_do.payload),
                workflow_messages=cast(
                    List[WorkflowMessage],
                    [self.get_message(wf_id) for wf_id in list(message_do.related_message_ids)]
                    or [],
                ),
                timestamp=int(message_do.timestamp),
            )
        if message_type == MessageType.TEXT_MESSAGE:
            return TextMessage(
                id=str(message_do.id),
                session_id=str(message_do.session_id),
                job_id=str(message_do.job_id),
                role=ChatMessageRole(str(message_do.role)),
                payload=str(message_do.payload),
                timestamp=int(message_do.timestamp),
                assigned_expert_name=str(message_do.assigned_expert_name),
            )
        if message_type == MessageType.FILE_MESSAGE:
            assert len(list(message_do.related_message_ids)) == 1, (
                f"File message {message_do.id} should have only one file id. "
                f"File id(s) :{list(message_do.related_message_ids)}"
            )
            return FileMessage(
                id=str(message_do.id),
                file_id=str(list(message_do.related_message_ids)[0]),
                session_id=str(message_do.session_id),
                timestamp=int(message_do.timestamp),
            )

        if message_type == MessageType.HYBRID_MESSAGE:
            instruction_results: List[TextMessageDo] = self.get_text_message_by_job_id_and_role(
                job_id=str(message_do.job_id), role=ChatMessageRole.USER
            )
            assert len(instruction_results) == 1, (
                f"Hybrid message {message_do.id} should have exactly one instruction message, "
                f"found {len(instruction_results)}. "
            )
            instruction_message: TextMessage = cast(
                TextMessage,
                self.parse_into_message(message_do=instruction_results[0]),
            )

            return HybridMessage(
                id=str(message_do.id),
                instruction_message=instruction_message,
                job_id=str(message_do.job_id),
                session_id=str(message_do.session_id),
                # load the attached messages from the database
                attached_messages=[
                    cast(FileMessage, self.get_message(id=str(attached_id)))
                    for attached_id in list(message_do.related_message_ids)
                ],
                timestamp=int(message_do.timestamp),
            )

        # TODO: support more message types
        raise ValueError(f"Unsupported message type: {message_type}")
