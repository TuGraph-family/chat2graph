from abc import ABC, abstractmethod
from typing import Any, List, Optional
from uuid import uuid4

from app.commom.type import MessageSourceType
from app.toolkit.tool.tool import FunctionCallResult


class Message(ABC):
    """Message"""

    def __init__(self, content: str, timestamp: str, id: Optional[str] = None):
        self._content: str = content
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


class AgentMessage(Message):
    """Agent message"""

    def __init__(
        self,
        content: str,
        timestamp: str,
        id: Optional[str] = None,
        source_type: MessageSourceType = MessageSourceType.MODEL,
        function_calls: Optional[List[FunctionCallResult]] = None,
    ):
        super().__init__(content=content, timestamp=timestamp, id=id)
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


class UserMessage(ABC):
    """User message"""

    def __init__(self, content: Any, timestamp: str, id: Optional[str] = None):
        self._id = id or str(uuid4())
        self._content: Any = None
        self._timestamp: str = ""

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

    # TODO: Add  user message attributes

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
