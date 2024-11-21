from abc import ABC, abstractmethod
from typing import List, Union

from app.memory.message import AgentMessage


class Memory(ABC):
    """Agent message memory."""

    def __init__(self):
        self._history_messages: List[AgentMessage] = []

    @abstractmethod
    def add_message(self, message: AgentMessage):
        """Add a message to the memory."""

    @abstractmethod
    def remove_message(self):
        """Remove a message from the memory."""

    @abstractmethod
    def upsert_message(self, index: int, message: AgentMessage):
        """Update a message in the memory."""

    @abstractmethod
    def get_messages(self) -> List[AgentMessage]:
        """Get a message from the memory."""

    @abstractmethod
    def clear_messages(self):
        """Clear all the messages in the memory."""

    @abstractmethod
    def get_message_by_index(self, index: int) -> AgentMessage:
        """Get a message by index."""

    @abstractmethod
    def get_message_by_id(self, message_id: str) -> Union[AgentMessage, None]:
        """Get a message by id."""

    @abstractmethod
    def get_message_metadata(self, message: AgentMessage) -> dict:
        """Get a message in json format."""

    @abstractmethod
    def get_messages_metadata(self) -> List[dict]:
        """Get all the messages in the memory in json format."""


class BuiltinMemory(Memory):
    """Agent message memory."""

    def add_message(self, message: AgentMessage):
        """Add a message to the memory."""
        self._history_messages.append(message)

    def remove_message(self):
        """Remove a message from the memory."""
        self._history_messages.pop()

    def upsert_message(self, index: int, message: AgentMessage):
        """Update a message in the memory."""
        self._history_messages[index] = message

    def get_messages(self) -> List[AgentMessage]:
        """Get a message from the memory."""
        return self._history_messages

    def clear_messages(self):
        """Clear all the messages in the memory."""
        self._history_messages.clear()

    def get_message_by_index(self, index: int) -> AgentMessage:
        """Get a message by index."""
        return self._history_messages[index]

    def get_message_by_id(self, message_id: str) -> Union[AgentMessage, None]:
        """Get a message by id."""
        for message in self._history_messages:
            if message.msg_id == message_id:
                return message

        return None

    def get_message_metadata(self, message: AgentMessage) -> dict:
        """Get a message in json format."""
        return message.__dict__

    def get_messages_metadata(self) -> List[dict]:
        """Get all the messages in the memory in json format."""
        return [message.__dict__ for message in self._history_messages]
