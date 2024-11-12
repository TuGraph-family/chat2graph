from typing import Any, List

from dbgpt.core.schema.api import ChatCompletionResponse, ChatMessage

from app.agent.base_agent.agent_adapter import AgentAdapter
from app.agent.base_agent.base_agent import BaseAgent
from app.memory.memory import Memory
from app.memory.message import AgentMessage


class DBGPTAdapter(AgentAdapter):
    """DB-GPT Adapter"""

    def __init__(self, base_agent: BaseAgent):
        self.base_agent = base_agent
        self.context = None
        self.memory: Memory = None

    async def receive_msg(
        self, message: AgentMessage, role: str = "user"
    ) -> AgentMessage:
        """Receive a message."""
        chat_message = ChatMessage(
            role=role,
            content=message.content,
        )
        await self.update_memory(chat_message)

        response: ChatCompletionResponse = (
            await self.base_agent.llm_client.chat_completion(
                self.memory.get_messages(), self.context
            )
        )
        return await self.parse_response(response)

    async def parse_response(self, response: Any):
        """Parse the response"""
        if response.tool_calls:
            return await self.handle_tool_call(response.tool_calls)
        return response.message.content

    async def handle_tool_call(self, tool_calls: List):
        """Handle the tool call."""

    async def update_memory(self, message: AgentMessage):
        """Update the memory."""
        self.memory.add_message(message)

    def set_memory(self, prompt: str):
        """Set the memory."""
        self.memory = Memory()
        self.memory.add_message(ChatMessage(role="system", content=prompt))
        return self.memory
