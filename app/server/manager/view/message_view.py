"""
Message view module for handling the transformation between internal message models
and API response formats.
"""

from typing import Any, Dict, List, TypeVar

from app.core.common.type import ChatMessageType
from app.core.model.message import AgentMessage, Message, TextMessage

T = TypeVar("T", bound=Message)


class MessageView:
    """Message view responsible for transforming internal message models to API response formats."""

    @staticmethod
    def serialize_message(message: Message) -> Dict[str, Any]:
        """Convert a Message model to an API response dictionary."""
        if isinstance(message, AgentMessage):
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "agent_result": message.get_workflow_result_message().get_payload(),
                "lesson": message.get_lesson(),
                "timestamp": message.get_timestamp(),
            }

        if isinstance(message, TextMessage):
            return {
                "id": message.get_id(),
                "session_id": message.get_session_id(),
                "message_type": ChatMessageType.TEXT.value,
                "job_id": message.get_job_id(),
                "role": message.get_role(),
                "message": message.get_payload(),
                "timestamp": message.get_timestamp(),
                "assigned_expert_name": message.get_assigned_expert_name(),
                "others": message.get_others(),
            }
        raise ValueError(f"Unsupported message type: {type(message)}")

    @staticmethod
    def serialize_messages(messages: List[T]) -> List[Dict[str, Any]]:
        """Serialize a list of messages to a list of API response dictionaries.

        Works with any list of objects that are Message subtypes.
        """
        return [MessageView.serialize_message(msg) for msg in messages]
