from typing import Any, Dict, List, TypeVar, cast

from attr import dataclass

from app.core.common.type import ChatMessageType
from app.core.dal.do.message_do import MessageType
from app.core.model.job_result import JobResult
from app.core.model.message import (
    AgentMessage,
    ChatMessage,
    FileMessage,
    HybridMessage,
    Message,
    TextMessage,
)
from app.server.manager.view.job_view import JobView

T = TypeVar("T", bound=Message)


@dataclass
class ConversationView:
    """A view class for managing conversation-related data.

    The ConversationView class serves as a container for storing and managing conversation
    elements including questions, answers, metrics, and intermediate thinking processes.

    Attributes:
        question (ChatMessage): The user's input/question message.
        answer (ChatMessage): The system's response/answer message.
        answer_metrics (JobResult): Performance metrics related to the answer generation.
        thinking_messages (List[AgentMessage]): List of intermediate reasoning msg by the agent.
        thinking_metrics (List[JobResult]): List of performance metrics for each thinking step.
    """

    question: ChatMessage
    answer: ChatMessage
    answer_metrics: JobResult
    thinking_messages: List[AgentMessage]
    thinking_metrics: List[JobResult]


class MessageView:
    """Message view responsible for transforming internal message models to API response formats.

    This class ensures that internal field names (like chat_message_type) are
    properly converted to API field names (like message_type) for consistent API responses.
    """

    @staticmethod
    def serialize_message(message: Message) -> Dict[str, Any]:
        """Convert a TextMessage model to an API response dictionary."""
        if isinstance(message, AgentMessage):
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "timestamp": message.get_timestamp(),
                "payload": message.get_payload() or "",
                "lesson": message.get_lesson(),
            }

        if isinstance(message, TextMessage):
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "timestamp": message.get_timestamp(),
                "payload": message.get_payload(),
                "message_type": ChatMessageType.TEXT.value,
                "role": message.get_role(),
                "session_id": message.get_session_id(),
                "assigned_expert_name": message.get_assigned_expert_name(),
            }
        raise ValueError(f"Unsupported message type: {type(message)}")

    @staticmethod
    def serialize_messages(messages: List[T]) -> List[Dict[str, Any]]:
        """Serialize a list of text messages to a list of API response dictionaries"""
        return [MessageView.serialize_message(msg) for msg in messages]

    @staticmethod
    def serialize_conversation_view(conversation_view: ConversationView) -> Dict[str, Any]:
        """Serialize a conversation view to an API response dictionary."""
        return {
            "question": {"message": MessageView.serialize_message(conversation_view.question)},
            "answer": {
                "message": MessageView.serialize_message(conversation_view.answer),
                "metrics": JobView.serialize_job_result(conversation_view.answer_metrics),
                "thinking": [
                    {
                        "message": MessageView.serialize_message(thinking_message),
                        "metrics": JobView.serialize_job_result(subjob_result),
                    }
                    for thinking_message, subjob_result in zip(
                        conversation_view.thinking_messages,
                        conversation_view.thinking_metrics,
                        strict=True,
                    )
                ],
            },
        }

    @staticmethod
    def deserialize_message(message: Dict[str, Any], message_type: MessageType) -> Message:
        """Convert a Message model to an API response dictionary."""
        if message_type == MessageType.TEXT_MESSAGE:
            return TextMessage(
                id=message.get("id", None),
                session_id=message["session_id"],
                job_id=message.get("job_id", None),
                role=message.get("role", "USER"),
                payload=message["payload"],
                timestamp=message.get("timestamp"),
                assigned_expert_name=message.get("assigned_expert_name", None),
            )
        if message_type == MessageType.FILE_MESSAGE:
            return FileMessage(
                file_id=message["file_id"],
                session_id=message["session_id"],
                id=message.get("id", None),
                timestamp=message.get("timestamp"),
            )
        if message_type == MessageType.HYBRID_MESSAGE:
            attached_messages: List[ChatMessage] = []
            # TODO: support more modal messages as the supplementary messages
            file_messages: List[FileMessage] = [
                cast(FileMessage, MessageView.deserialize_message(msg, MessageType.FILE_MESSAGE))
                for msg in message["attached_messages"]
                if msg["type"] == ChatMessageType.FILE and isinstance(msg, dict)
            ]
            attached_messages.extend(file_messages)

            return HybridMessage(
                timestamp=message.get("timestamp"),
                id=message.get("id", None),
                job_id=message.get("job_id", None),
                session_id=message.get("session_id", None),
                attached_messages=attached_messages,
            )
        raise ValueError(f"Unsupported message type: {message['message_type']}")
