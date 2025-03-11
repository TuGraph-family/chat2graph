from typing import Any, Dict

from app.core.dal.do.message_do import MessageType
from app.core.model.message import Message, TextMessage


class SessionView:
    """Message view responsible for transforming internal message models to API response formats."""

    @staticmethod
    def deserialize_message(message: Dict[str, Any], message_type: MessageType) -> Message:
        """Convert a Message model to an API response dictionary."""
        if message_type == MessageType.TEXT_MESSAGE:
            return TextMessage(
                id=message.get("id", None),
                session_id=message["session_id"],
                job_id=message.get("job_id", None),
                role=message.get("role", "user"),
                payload=message["message"],
                timestamp=message.get("timestamp"),
                assigned_expert_name=message.get("assigned_expert_name", None),
                others=message.get("others", None),
            )
        raise ValueError(f"Unsupported message type: {message['message_type']}")
