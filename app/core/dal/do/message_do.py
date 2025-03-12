from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Column, String, Text, func

from app.core.dal.database import Do
from app.core.model.message import MessageType


class MessageDo(Do):  # type: ignore
    """Base message class"""

    __tablename__ = "message"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(BigInteger, server_default=func.strftime("%s", "now"))

    job_id = Column(String(36), nullable=False)  # FK constraint

    type = Column(
        String(50), nullable=False
    )  # identify the type to be used in polymorphic message queries (e.g. ModelMessageAO)

    resource_id = Column(String(36), nullable=True)  # FK constraint
    resource_type = Column(String(50), nullable=True)
    target_id = Column(String(36), nullable=True)  # FK constraint
    target_type = Column(String(50), nullable=True)

    # all possible fields from all message types in a single table

    # model message fields
    payload = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)
    function_calls_json = Column(JSON, nullable=True)

    # common fields shared by multiple types
    session_id = Column(String(36), nullable=True)  # FK constraint

    # model message specific fields
    operator_id = Column(String(36), nullable=True)  # FK constraint
    step = Column(String(50), nullable=True)

    # agent message fields
    lesson = Column(Text, nullable=True)
    related_message_ids = Column(JSON, nullable=True)

    # chat/text message fields
    role = Column(String(50), nullable=True)
    assigned_expert_name = Column(String(100), nullable=True)
    others = Column(Text, nullable=True)

    __mapper_args__ = {
        "polymorphic_on": type,
    }


class ModelMessageAO(MessageDo):
    """Model message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.MODEL_MESSAGE.value,  # type: ignore
    }


class WorkflowMessageDo(MessageDo):
    """Workflow message, used to communicate between the operators in the workflow."""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.WORKFLOW_MESSAGE.value,  # type: ignore
    }


class AgentMessageDo(MessageDo):
    """agent message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.AGENT_MESSAGE.value,  # type: ignore
    }


class ChatMessageDo(MessageDo):
    """chat message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.CHAT_MESSAGE.value,  # type: ignore
    }


class TextMessageDo(ChatMessageDo):
    """text message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.TEXT_MESSAGE.value,  # type: ignore
    }
