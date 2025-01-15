from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.commom.type import MessageSourceType
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
        content: str,
        timestamp: str,
        id: Optional[str] = None,
        source_type: MessageSourceType = MessageSourceType.MODEL,
        function_calls: Optional[List[FunctionCallResult]] = None,
    ):
        super().__init__(timestamp=timestamp, id=id)
        self._content: str = content
        self._source_type: MessageSourceType = source_type
        self._function_calls: Optional[List[FunctionCallResult]] = function_calls

    def get_payload(self) -> str:
        """Get the content of the message."""
        return self._content

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
        content: Dict[str, Any],
        timestamp: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"), id=id)
        self._content: Dict[str, Any] = content
        for key, value in content.items():
            setattr(self, key, value)

    def get_payload(self) -> Dict[str, Any]:
        """Get the content of the message."""
        return self._content

    def __getattr__(self, name: str) -> Any:
        """Dynamic field access through attributes."""
        if name in self._content:
            return self._content[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """Dynamic field setting through attributes."""
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            if hasattr(self, "_content"):
                self._content[name] = value
            else:
                super().__setattr__(name, value)

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id


class UserMessage(Message):
    """User message"""

    def __init__(self, timestamp: str, id: Optional[str] = None):
        self._id = id or str(uuid4())
        self._timestamp: str = timestamp

    @abstractmethod
    def get_payload(self) -> Any:
        """Get the content of the message."""

    @abstractmethod
    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""

    @abstractmethod
    def get_id(self) -> str:
        """Get the message id."""


class UserTextMessage(UserMessage):
    """User message"""

    # TODO: Add user message attributes

    def get_payload(self) -> Any:
        """Get the content of the message."""
        return None

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id

    def get_text(self) -> str:
        """Get the string content of the message."""
        # TODO: Implement get_text
        return ""
