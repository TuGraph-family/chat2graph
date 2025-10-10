from abc import ABC, abstractmethod
from typing import Any, List, Optional, Union

from app.core.model.message import ModelMessage
from app.core.model.task import MemoryKey


class Memory(ABC):
    """Agent memory."""

    def __init__(self) -> None:
        self._history_messages: List[ModelMessage] = []

    @abstractmethod
    def add_message(self, message: ModelMessage) -> None:
        """Add a message to the memory."""

    @abstractmethod
    def remove_message(self) -> None:
        """Remove a message from the memory."""

    @abstractmethod
    def upsert_message(self, index: int, message: ModelMessage) -> None:
        """Update a message in the memory."""

    @abstractmethod
    def get_messages(self) -> List[ModelMessage]:
        """Get a message from the memory."""

    @abstractmethod
    def clear_messages(self) -> None:
        """Clear all the messages in the memory."""

    @abstractmethod
    def get_message_by_index(self, index: int) -> ModelMessage:
        """Get a message by index."""

    @abstractmethod
    def get_message_by_id(self, message_id: str) -> Union[ModelMessage, None]:
        """Get a message by id."""

    @abstractmethod
    def retrieve(self, memory_key: MemoryKey, query_text: str) -> List[Any]:
        """Retrieve relevant memories.

        Args:
            query_text (str): The query text used to retrieve memories.
            top_k (int): The maximum number of memories to return.

        Returns:
            List[str]: Retrieved memory snippets. Empty list if unsupported.
        """

    @abstractmethod
    def memorize(self, memory_key, memory_text: str, result: str) -> None:
        """Persist a conversation turn to the memory backend.

        Implementations may choose to be no-ops. Should never raise.

        Args:
            sys_prompt (str): The system prompt used for generation.
            messages (List[ModelMessage]): The message history for the turn.
            job_id (str): The job id scope.
            operator_id (str): The operator id scope.
        """


class BuiltinMemory(Memory):
    """Agent message memory."""

    def add_message(self, message: ModelMessage):
        """Add a message to the memory."""
        self._history_messages.append(message)

    def remove_message(self):
        """Remove a message from the memory."""
        self._history_messages.pop()

    def upsert_message(self, index: int, message: ModelMessage):
        """Update a message in the memory."""
        self._history_messages[index] = message

    def get_messages(self) -> List[ModelMessage]:
        """Get a message from the memory."""
        return self._history_messages

    def clear_messages(self):
        """Clear all the messages in the memory."""
        self._history_messages.clear()

    def get_message_by_index(self, index: int) -> ModelMessage:
        """Get a message by index."""
        return self._history_messages[index]

    def get_message_by_id(self, message_id: str) -> Optional[ModelMessage]:
        """Get a message by id."""
        for message in self._history_messages:
            if message.get_id() == message_id:
                return message

        return None

    def retrieve(self, memory_key: MemoryKey, query_text: str) -> List[Any]:
        """Retrieve relevant memories (no-op for builtin memory)."""
        return []

    def memorize(self, memory_key: MemoryKey, memory_text: str, result: str) -> None:
        """Persist a conversation turn (no-op for builtin memory)."""
        return None