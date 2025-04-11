from typing import Any, Dict, List, Optional, TypeVar, cast

from attr import dataclass

from app.core.common.type import ChatMessageRole, ChatMessageType
from app.core.dal.do.message_do import MessageType
from app.core.model.file_descriptor import FileDescriptor
from app.core.model.job import SubJob
from app.core.model.job_result import JobResult
from app.core.model.message import (
    AgentMessage,
    ChatMessage,
    FileMessage,
    GraphMessage,
    HybridMessage,
    Message,
    TextMessage,
)
from app.server.manager.view.job_view import JobView

T = TypeVar("T", bound=Message)


@dataclass
class MessageView:
    """A view class for managing conversation-related data.

    The ConversationView class serves as a container for storing and managing conversation
    elements including questions, answers, metrics, and intermediate thinking processes.

    Attributes:
        question (ChatMessage): The user's input/question message.
        answer (ChatMessage): The system's response/answer message.
        answer_metrics (JobResult): Performance metrics related to the answer generation.
        thinking_messages (List[AgentMessage]): List of intermediate reasoning msg by the agent.
        thinking_subjobs (List[SubJob]): List of subjobs for each thinking step.
        thinking_metrics (List[JobResult]): List of performance metrics for each thinking step.
    """

    question: ChatMessage
    answer: ChatMessage
    answer_metrics: JobResult
    thinking_messages: List[AgentMessage]
    thinking_subjobs: List[SubJob]
    thinking_metrics: List[JobResult]


class MessageViewTransformer:
    """Message view transformer responsible for transforming internal message models to API response
        formats.

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
                "payload": (message.get_payload() or "")
                .replace("<task_objective>", "")
                .replace("</task_objective>", "")
                .replace("<task_context>", "")
                .replace("</task_context>", "")
                .replace("<key_reasoning_points>", "")
                .replace("</key_reasoning_points>", "")
                .replace("<final_output>", "")
                .replace("</final_output>", ""),
                "lesson": message.get_lesson(),
            }

        if isinstance(message, TextMessage):
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "session_id": message.get_session_id(),
                "timestamp": message.get_timestamp(),
                "payload": message.get_payload(),
                "message_type": ChatMessageType.TEXT.value,
                "role": message.get_role().value,
                "assigned_expert_name": message.get_assigned_expert_name(),
            }

        if isinstance(message, FileMessage):
            descriptor: Optional[FileDescriptor] = message.get_descriptor()
            if descriptor is None:
                raise ValueError(f"File message {message.get_id()} has no descriptor.")
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "session_id": message.get_session_id(),
                "timestamp": message.get_timestamp(),
                "file_id": message.get_file_id(),
                "message_type": ChatMessageType.FILE.value,
                "name": descriptor.name,  # required by the frontend
                "size": descriptor.size,  # required by the frontend
            }

        if isinstance(message, GraphMessage):
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "session_id": message.get_session_id(),
                "timestamp": message.get_timestamp(),
                "payload": GraphMessage.serialize_payload(message.get_payload()),
                "message_type": ChatMessageType.GRAPH.value,
            }

        if isinstance(message, HybridMessage):
            return {
                "id": message.get_id(),
                "job_id": message.get_job_id(),
                "session_id": message.get_session_id(),
                "timestamp": message.get_timestamp(),
                "instruction_message": MessageViewTransformer.serialize_message(
                    message.get_instruction_message()
                ),
                "attached_messages": [
                    MessageViewTransformer.serialize_message(msg)
                    for msg in message.get_attached_messages()
                ],
            }

        raise ValueError(f"Unsupported message type: {type(message)}")

    @staticmethod
    def serialize_messages(messages: List[T]) -> List[Dict[str, Any]]:
        """Serialize a list of text messages to a list of API response dictionaries"""
        return [MessageViewTransformer.serialize_message(msg) for msg in messages]

    @staticmethod
    def serialize_conversation_view(conversation_view: MessageView) -> Dict[str, Any]:
        """Serialize a conversation view to an API response dictionary."""
        return {
            "question": {
                "message": MessageViewTransformer.serialize_message(conversation_view.question)
            },
            "answer": {
                "message": MessageViewTransformer.serialize_message(conversation_view.answer),
                "metrics": JobView.serialize_job_result(conversation_view.answer_metrics),
                "thinking": [
                    {
                        "message": MessageViewTransformer.serialize_message(thinking_message),
                        "job": JobView.serialize_job(job=thinking_subjob),
                        "metrics": JobView.serialize_job_result(subjob_result),
                    }
                    for thinking_message, thinking_subjob, subjob_result in zip(
                        conversation_view.thinking_messages,
                        conversation_view.thinking_subjobs,
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
                role=ChatMessageRole(message.get("role", ChatMessageRole.USER.value)),
                payload=message["payload"],
                timestamp=message.get("timestamp"),
                assigned_expert_name=message.get("assigned_expert_name", None),
            )
        if message_type == MessageType.FILE_MESSAGE:
            return FileMessage(
                file_id=message["file_id"],
                session_id=message["session_id"],
                id=message.get("id", None),
                timestamp=message.get("timestamp", None),
            )
        if message_type == MessageType.HYBRID_MESSAGE:
            # format the instruction message
            instruction_message: ChatMessage
            text_messages: TextMessage = cast(
                TextMessage,
                MessageViewTransformer.deserialize_message(
                    message["instruction_message"], MessageType.TEXT_MESSAGE
                )
                if message["instruction_message"]["message_type"] == ChatMessageType.TEXT.value
                else None,
            )
            instruction_message = text_messages

            # format the attached messages
            attached_messages: List[ChatMessage] = []
            file_messages: List[FileMessage] = [
                cast(
                    FileMessage,
                    MessageViewTransformer.deserialize_message(msg, MessageType.FILE_MESSAGE),
                )
                for msg in message["attached_messages"]
                if msg["message_type"] == ChatMessageType.FILE.value
            ]
            attached_messages.extend(file_messages)

            return HybridMessage(
                instruction_message=instruction_message,
                timestamp=message.get("timestamp", None),
                id=message.get("id", None),
                job_id=message.get("job_id", None),
                session_id=instruction_message.get_session_id(),
                attached_messages=attached_messages,
            )
        # TODO: support more modal messages as the attatched messages
        raise ValueError(f"Unsupported message type: {message['message_type']}")
