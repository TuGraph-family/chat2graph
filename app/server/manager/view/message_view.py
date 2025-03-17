from typing import Any, Dict, List, TypeVar, cast

from app.core.common.type import ChatMessageType
from app.core.dal.do.message_do import MessageType
from app.core.model.message import (
    AgentMessage,
    ChatMessage,
    FileMessage,
    HybridMessage,
    Message,
    TextMessage,
)

T = TypeVar("T", bound=Message)


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
                payload=message["payload"],
                session_id=message["session_id"],
                id=message.get("id", None),
                timestamp=message.get("timestamp"),
            )
        if message_type == MessageType.HYBRID_MESSAGE:
            supplementary_messages: List[ChatMessage] = []
            # TODO: support more modal messages as the supplementary messages
            file_messages: List[FileMessage] = [
                cast(FileMessage, MessageView.deserialize_message(msg, MessageType.FILE_MESSAGE))
                for msg in message["supplementary_messages"]
                if msg["type"] == ChatMessageType.FILE and isinstance(msg, dict)
            ]
            supplementary_messages.extend(file_messages)

            return HybridMessage(
                timestamp=message.get("timestamp"),
                id=message.get("id", None),
                job_id=message.get("job_id", None),
                session_id=message.get("session_id", None),
                supplementary_messages=supplementary_messages,
            )
        raise ValueError(f"Unsupported message type: {message['message_type']}")
