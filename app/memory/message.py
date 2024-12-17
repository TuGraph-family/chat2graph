import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.commom.type import MessageSourceType
from app.toolkit.tool.tool import FunctionCallResult


class Tracable(ABC):
    """Interface for the tracable message."""

    def __init__(self, timestamp: str, id: Optional[str] = None):
        self._timestamp: str = timestamp
        self._id: str = id or str(uuid4())

    @abstractmethod
    def get_payload(self) -> str:
        """Get the content of the message."""

    @abstractmethod
    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""

    @abstractmethod
    def get_id(self) -> str:
        """Get the message id."""


class ModelMessage(Tracable):
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


class WorkflowMessage(Tracable):
    """Workflow message, used to communicate between the operators in the workflow."""

    def __init__(
        self,
        metadata: Dict[str, Any],
        timestamp: Optional[str] = None,
        id: Optional[str] = None,
    ):
        super().__init__(
            timestamp=timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ"), id=id
        )
        self._metadata: Dict[str, Any] = metadata

    def get_payload(self) -> Dict[str, Any]:
        """Get the content of the message."""
        return self._metadata

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_id(self) -> str:
        """Get the message id."""
        return self._id


class UserMessage(Tracable):
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
