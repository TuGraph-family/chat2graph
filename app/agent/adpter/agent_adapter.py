from abc import ABC, abstractmethod
from typing import List

from app.memory.message import AgentMessage


class AgentAdapter(ABC):
    """Agent adapter."""

    @abstractmethod
    async def init_client(self):
        """Initialize the LLM client."""

    @abstractmethod
    async def receive_message(self, message: AgentMessage) -> AgentMessage:
        """Receive a message."""

    @abstractmethod
    async def parse_response(self, response: AgentMessage):
        """Parse the response."""

    @abstractmethod
    async def handle_tool_call(self, tool_calls: List):
        """Handle the tool call."""

    @abstractmethod
    async def update_memory(self, message: AgentMessage):
        """Update the memory."""
