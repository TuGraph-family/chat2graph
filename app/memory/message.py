from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agent.job import Job
from app.common.type import MessageSourceType
from app.toolkit.tool.tool import FunctionCallResult


class Message(ABC):
    """Interface for the Message message."""

    def __init__(self, timestamp: str, id: Optional[str] = None):
        self._timestamp: str = timestamp
        self._id: str = id or str(uuid4())

    @abstractmethod
    def get_payload(self) -> Any:
        """Get the content of the message."""

    @abstractmethod
    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""

    @abstractmethod
    def get_id(self) -> str:
        """Get the message id."""


class ModelMessage(Message):
    """Agent message"""

    def __init__(
        self,
        payload: str,
        timestamp: str,
        id: Optional[str] = None,
        source_type: MessageSourceType = MessageSourceType.MODEL,
        function_calls: Optional[List[FunctionCallResult]] = None,
    ):
        super().__init__(timestamp=timestamp, id=id)
        self._payload: str = payload
        self._source_type: MessageSourceType = source_type
        self._function_calls: Optional[List[FunctionCallResult]] = function_calls

    def get_payload(self) -> str:
        """Get the content of the message."""
        return self._payload

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id

    def get_source_type(self) -> MessageSourceType:
        """Get the source type of the message."""
        return self._source_type

    def get_function_calls(self) -> Optional[List[FunctionCallResult]]:
        """Get the function of the message."""
        return self._function_calls

    def set_source_type(self, source_type: MessageSourceType):
        """Set the source type of the message."""
        self._source_type = source_type


class WorkflowMessage(Message):
    """Workflow message, used to communicate between the operators in the workflow."""

    def __init__(
        self,
        payload: Dict[str, Any],
        timestamp: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"), id=id)
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

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id


class AgentMessage(Message):
    """Agent message"""

    def __init__(
        self,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
        timestamp: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"), id=id)
        self._job: Job = job
        self._workflow_messages: List[WorkflowMessage] = workflow_messages or []
        self._lesson: Optional[str] = lesson

    def get_payload(self) -> Job:
        """Get the content of the message."""
        return self._job

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

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id

    def set_lesson(self, lesson: str):
        """Set the lesson of the execution of the job."""
        self._lesson = lesson


class ChatMessage(Message):
    """Chat message"""

    def __init__(
        self,
        payload: Any,
        timestamp: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"), id=id)
        self._payload: str = payload

    def get_payload(self) -> str:
        """Get the content of the message."""
        return self._payload

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id


class TextMessage(ChatMessage):
    """Text message"""

    def __init__(
        self,
        payload: str,
        timestamp: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(payload=payload, timestamp=timestamp, id=id)

    def get_payload(self) -> Any:
        """Get the content of the message."""
        return self._payload

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id

    def get_text(self) -> str:
        """Get the string content of the message."""
        return self._payload
