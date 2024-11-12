from abc import ABC, abstractmethod
from typing import List

from app.memory.memory import Memory
from app.memory.message import AgentMessage


class BaseAgent(ABC):
    """"""

    def __init__(self):
        """"""
        self.id = None
        self.memory: Memory = None
        self.system_prompt: str = None

        self.function_list: List = None

        self.llm_config = None
        self.llm_client = None

    @abstractmethod
    async def execute(self, message: AgentMessage) -> AgentMessage:
        """Execute the message by calling the LLM or the tools."""

    @abstractmethod
    def add_tool(self, *args, **kwargs):
        """Add a tool to the function calling list."""

    @abstractmethod
    def remove_tool(self, *args, **kwargs):
        """Remove a tool from the function calling list."""

    @abstractmethod
    def handle_memory(self):
        """Handle the memory."""

    @abstractmethod
    def set_system_prompt(self, prompt: str):
        """Set the system prompt."""
