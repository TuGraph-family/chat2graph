from enum import Enum
import time
from uuid import uuid4

from sqlalchemy import JSON, Column, ForeignKey, String, Table, Text

from app.core.dal.database import Base


class MessageType(Enum):
    """Message types"""

    MODEL_MESSAGE = "ModelMessage"
    WORKFLOW_MESSAGE = "WorkflowMessage"
    AGENT_MESSAGE = "AgentMessage"
    CHAT_MESSAGE = "ChatMessage"
    TEXT_MESSAGE = "TextMessage"


# agent workflow relationship table
agent_workflow_links = Table(
    "agent_workflow_links",
    Base.metadata,
    Column(
        "agent_message_id",
        String(36),
        ForeignKey("message.id", use_alter=True, name="fk_agent_message"),
        primary_key=True,
    ),
    Column(
        "workflow_message_id",
        String(36),
        ForeignKey("message.id", use_alter=True, name="fk_workflow_message"),
        primary_key=True,
    ),
)


class MessageModel(Base):
    """Base message class"""

    __tablename__ = "message"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(
        String(30), nullable=False, default=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    type = Column(String(50), nullable=False)  # identify the type to be used in polymorphic queries

    # all possible fields from all message types in a single table

    # model message fields
    payload = Column(Text, nullable=True)
    source_type = Column(String(50), nullable=True)
    function_calls_json = Column(JSON, nullable=True)

    # workflow message fields
    payload_json = Column(JSON, nullable=True)

    # common fields shared by multiple types
    session_id = Column(
        String(36),
        ForeignKey("session.id", use_alter=True, name="fk_message_session", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = Column(
        String(36), ForeignKey("job.id", use_alter=True, name="fk_message_job"), nullable=True
    )

    # model message specific fields
    operator_id = Column(String(36), nullable=True)  # TODO: set the FK constraint
    step = Column(String(50), nullable=True)

    # agent message fields
    lesson = Column(Text, nullable=True)
    linked_workflow_ids = Column(JSON, nullable=True)  # store workflow ids as json array

    # chat/text message fields
    chat_message_type = Column(String(50), nullable=True)
    role = Column(String(50), nullable=True)
    assigned_expert_name = Column(String(100), nullable=True)
    others = Column(Text, nullable=True)

    # relationship definitions
    # TODO: files = relationship("FileModel", backref="message", cascade="all, delete-orphan")

    __mapper_args__ = {
        "polymorphic_on": type,
    }


class ModelMessageModel(MessageModel):
    """Model message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.MODEL_MESSAGE.value,
    }


class WorkflowMessageModel(MessageModel):
    """Workflow message, used to communicate between the operators in the workflow."""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.WORKFLOW_MESSAGE.value,
    }


class AgentMessageModel(MessageModel):
    """agent message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.AGENT_MESSAGE.value,
    }


class ChatMessageModel(MessageModel):
    """chat message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.CHAT_MESSAGE.value,
        # "polymorphic_on": "chat_message_type",
    }


class TextMessageModel(ChatMessageModel):
    """text message"""

    __mapper_args__ = {
        "polymorphic_identity": MessageType.TEXT_MESSAGE.value,
    }
