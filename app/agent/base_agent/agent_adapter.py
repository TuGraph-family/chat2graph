from abc import ABC, abstractmethod
from typing import Any, List

from app.memory.message import AgentMessage


class AgentAdapter(ABC):
    """Agent adapter."""

    @abstractmethod
    def init_client(self):
        """Initialize the LLM client."""

    @abstractmethod
    async def receive_msg(self, message: AgentMessage, role: str = "user"):
        """Receive a message."""

    @abstractmethod
    async def parse_response(self, response: Any):
        """Parse the response."""

    @abstractmethod
    async def handle_tool_call(self, tool_calls: List):
        """Handle the tool call."""

    @abstractmethod
    async def update_memory(self, message: AgentMessage):
        """Update the memory."""
