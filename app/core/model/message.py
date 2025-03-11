from abc import ABC, abstractmethod
from enum import Enum
import json
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.common.type import MessageSourceType, WorkflowStatus
from app.core.toolkit.tool import FunctionCallResult


class MessageType(Enum):
    """Message types"""

    MODEL_MESSAGE = "ModelMessage"
    WORKFLOW_MESSAGE = "WorkflowMessage"
    AGENT_MESSAGE = "AgentMessage"
    CHAT_MESSAGE = "ChatMessage"
    TEXT_MESSAGE = "TextMessage"


class Message(ABC):
    """Interface for the Message message."""

    def __init__(self, job_id: str, timestamp: Optional[int], id: Optional[str] = None):
        self._timestamp: Optional[int] = timestamp
        self._id: str = id or str(uuid4())
        self._job_id: str = job_id

    def get_timestamp(self) -> Optional[int]:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id

    def get_job_id(self) -> str:
        """Get the job ID."""
        return self._job_id

    @abstractmethod
    def copy(self) -> "Message":
        """Copy the message."""


class ModelMessage(Message):
    """Agent message"""

    def __init__(
        self,
        payload: str,
        job_id: str,
        step: int,
        timestamp: Optional[int] = None,
        id: Optional[str] = None,
        source_type: MessageSourceType = MessageSourceType.MODEL,
        function_calls: Optional[List[FunctionCallResult]] = None,
    ):
        super().__init__(job_id=job_id, timestamp=timestamp, id=id)
        self._payload: str = payload
        self._step: int = step
        self._source_type: MessageSourceType = source_type
        self._function_calls: Optional[List[FunctionCallResult]] = function_calls

    def get_payload(self) -> str:
        """Get the content of the message."""
        return self._payload

    def get_step(self) -> int:
        """Get the step of the message."""
        return self._step

    def get_source_type(self) -> MessageSourceType:
        """Get the source type of the message."""
        return self._source_type

    def get_function_calls(self) -> Optional[List[FunctionCallResult]]:
        """Get the function of the message."""
        return self._function_calls

    def set_source_type(self, source_type: MessageSourceType):
        """Set the source type of the message."""
        self._source_type = source_type

    def copy(self) -> Any:
        """Copy the message."""
        return ModelMessage(
            payload=self._payload,
            job_id=self._job_id,
            step=self._step,
            timestamp=self._timestamp,
            id=self._id,
            source_type=self._source_type,
            function_calls=self._function_calls,
        )


class WorkflowMessage(Message):
    """Workflow message, used to communicate between the operators in the workflow."""

    def __init__(
        self,
        payload: Dict[str, Any],
        job_id=str,
        timestamp: Optional[int] = None,
        id: Optional[str] = None,
    ):
        super().__init__(timestamp=timestamp, id=id, job_id=job_id)
        self._payload: Dict[str, Any] = payload
        for key, value in payload.items():
            setattr(self, key, value)

    def get_payload(self) -> Dict[str, Any]:
        """Get the content of the message."""
        return self._payload

    def __getattr__(self, name: str) -> Any:
        """Dynamic field access through attributes."""
        if name in self._payload:
            return self._payload[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Dynamic field setting through attributes."""
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            if hasattr(self, "_payload"):
                self._payload[name] = value
            else:
                super().__setattr__(name, value)

    def copy(self) -> "WorkflowMessage":
        """Copy the message."""
        return WorkflowMessage(
            payload=self._payload.copy(),
            timestamp=self._timestamp,
            id=self._id,
            job_id=self._job_id,
        )

    @staticmethod
    def serialize_payload(payload: Dict[str, Any]) -> str:
        """Serialize the payload."""

        def enum_handler(obj):
            if isinstance(obj, Enum):
                return obj.value
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        return json.dumps(payload, default=enum_handler)

    @staticmethod
    def deserialize_payload(payload: str) -> Dict[str, Any]:
        """Deserialize the payload."""
        payload_dict = json.loads(payload)
        if "status" in payload_dict:
            payload_dict["status"] = WorkflowStatus(payload_dict["status"])
        return payload_dict


class AgentMessage(Message):
    """Agent message"""

    def __init__(
        self,
        job_id: str,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
        timestamp: Optional[int] = None,
        id: Optional[str] = None,
    ):
        super().__init__(job_id=job_id, timestamp=timestamp, id=id)
        self._workflow_messages: List[WorkflowMessage] = workflow_messages or []
        self._lesson: Optional[str] = lesson

    def get_workflow_messages(self) -> List[WorkflowMessage]:
        """Get the workflow messages of the execution results of the previous jobs."""
        return self._workflow_messages

    def get_workflow_result_message(self) -> WorkflowMessage:
        """Get the workflow result message of the execution results of the previous jobs.
        Only one workflow result message is expected, because the message represents the result of
        the workflow of the agent.
        """
        if len(self._workflow_messages) != 1:
            raise ValueError("The agent message received no or multiple workflow result messages.")
        return self._workflow_messages[0]

    def get_lesson(self) -> Optional[str]:
        """Get the lesson of the execution of the job."""
        return self._lesson

    def set_lesson(self, lesson: str):
        """Set the lesson of the execution of the job."""
        self._lesson = lesson

    def copy(self) -> "AgentMessage":
        """Copy the message."""
        return AgentMessage(
            job_id=self._job_id,
            workflow_messages=self._workflow_messages.copy(),
            lesson=self._lesson,
            timestamp=self._timestamp,
            id=self._id,
        )


class ChatMessage(Message):
    """Chat message

    Attributes:
        _id str: Unique identifier for the message
        _timestamp int: Timestamp of the message (defaults to current UTC time)
        _payload (Any): The content of the message
        _session_id (Optional[str]): ID of the associated session
        _others (Optional[str]): Additional information
        _assigned_expert_name (Optional[str]): Name of the assigned expert
    """

    def __init__(
        self,
        payload: Any,
        job_id: str,
        timestamp: Optional[int] = None,
        id: Optional[str] = None,
        session_id: Optional[str] = None,
        others: Optional[str] = None,
        assigned_expert_name: Optional[str] = None,
    ):
        super().__init__(job_id=job_id, timestamp=timestamp, id=id)
        self._payload: Any = payload
        self._session_id: Optional[str] = session_id
        self._others: Optional[str] = others
        self._assigned_expert_name: Optional[str] = assigned_expert_name

    def get_payload(self) -> Any:
        """Get the content of the message."""
        return self._payload

    def get_timestamp(self) -> Optional[int]:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id

    def get_session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self._session_id

    def get_others(self) -> Optional[str]:
        """Get the additional information."""
        return self._others

    def get_assigned_expert_name(self) -> Optional[str]:
        """Get the assigned expert name."""
        return self._assigned_expert_name

    def set_assigned_expert_name(self, assigned_expert_name: str):
        """Set the assigned expert name."""
        self._assigned_expert_name = assigned_expert_name

    def copy(self) -> "ChatMessage":
        """Copy the message."""
        return ChatMessage(
            payload=self._payload,
            job_id=self._job_id,
            timestamp=self._timestamp,
            id=self._id,
            session_id=self._session_id,
            others=self._others,
        )


class TextMessage(ChatMessage):
    """Text message"""

    def __init__(
        self,
        payload: str,
        job_id: Optional[str] = None,
        timestamp: Optional[int] = None,
        id: Optional[str] = None,
        session_id: Optional[str] = None,
        role: Optional[str] = None,
        others: Optional[str] = None,
        assigned_expert_name: Optional[str] = None,
    ):
        super().__init__(
            payload=payload,
            job_id=job_id or "temp_job_id",
            timestamp=timestamp,
            id=id,
            session_id=session_id,
            others=others,
            assigned_expert_name=assigned_expert_name,
        )
        self._role: Optional[str] = role

    def get_payload(self) -> str:
        """Get the string content of the message."""
        return self._payload

    def get_role(self) -> Optional[str]:
        """Get the role."""
        return self._role

    def copy(self) -> "TextMessage":
        """Copy the message."""
        return TextMessage(
            payload=self._payload,
            job_id=self._job_id,
            timestamp=self._timestamp,
            id=self._id,
            session_id=self._session_id,
            role=self._role,
            assigned_expert_name=self._assigned_expert_name,
            others=self._others,
        )
