from abc import ABC
from typing import List, Union

from app.memory.message import AgentMessage


class Memory(ABC):
    """Agent message memory."""

    def __init__(self):
        self.history_messages: List[AgentMessage] = []

    def is_empty(self) -> bool:
        """Check if the memory is empty."""
        return len(self.history_messages) == 0

    def add_message(self, message: AgentMessage):
        """Add a message to the memory."""
        self.history_messages.append(message)

    def remove_message(self):
        """Remove a message from the memory."""
        self.history_messages.pop()

    def upsert_message(self, index: int, message: AgentMessage):
        """Update a message in the memory."""
        self.history_messages[index] = message

    def get_messages(self) -> List[AgentMessage]:
        """Get a message from the memory."""
        return self.history_messages

    def clear_messages(self):
        """Clear all the messages in the memory."""
        self.history_messages.clear()

    def get_message_by_index(self, index: int) -> AgentMessage:
        """Get a message by index."""
        return self.history_messages[index]

    def get_message_by_id(self, message_id: str) -> Union[AgentMessage, None]:
        """Get a message by id."""
        for message in self.history_messages:
            if message.msg_id == message_id:
                return message

        return None

    def get_message_metadata(self, message: AgentMessage) -> dict:
        """Get a message in json format."""
        return message.__dict__

    def get_messages_metadata(self) -> List[dict]:
        """Get all the messages in the memory in json format."""
        return [message.__dict__ for message in self.history_messages]
