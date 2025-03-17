from typing import Any, Dict, List, TypeVar

from app.core.common.type import ChatMessageType
from app.core.model.message import AgentMessage, Message, TextMessage

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
