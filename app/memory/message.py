from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import uuid4

from app.commom.type import MessageSourceType


class Message(ABC):
    """Message"""

    def __init__(self, content: str, timestamp: str, message_id: str = str(uuid4())):
        self._content: str = content
        self._timestamp: str = timestamp
        self._message_id: str = message_id

    @abstractmethod
    def get_content(self) -> str:
        """Get the content of the message."""

    @abstractmethod
    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""

    @abstractmethod
    def get_message_id(self) -> str:
        """Get the message id."""


class AgentMessage(Message):
    """Agent message"""

    def __init__(
        self,
        content: str,
        timestamp: str,
        message_id: str = str(uuid4()),
        source_type: MessageSourceType = MessageSourceType.MODEL,
        function: Optional[Dict[str, Any]] = None,
        tool_log: Optional[str] = None,
    ):
        super().__init__(content, timestamp, message_id)
        self._source_type: MessageSourceType = source_type
        self._function: Optional[Dict[str, Any]] = function
        self._tool_log: Optional[str] = tool_log

    def get_content(self) -> str:
        """Get the content of the message."""
        return self._content

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""
        return self._timestamp

    def get_message_id(self) -> str:
        """Get the message id."""
        return self._message_id

    def get_source_type(self) -> MessageSourceType:
        """Get the source type of the message."""
        return self._source_type

    def get_function(self) -> Optional[Dict[str, Any]]:
        """Get the function of the message."""
        return self._function

    def get_tool_log(self) -> Optional[str]:
        """Get the tool log of the message."""
        return self._tool_log

    def set_source_type(self, source_type: MessageSourceType):
        """Set the source type of the message."""
        self._source_type = source_type


class UserMessage(Message):
    """User message"""

    # TODO: Add user message attributes
    def get_content(self) -> str:
        """Get the content of the message."""

    def get_timestamp(self) -> str:
        """Get the timestamp of the message."""

    def get_message_id(self) -> str:
        """Get the message id."""
