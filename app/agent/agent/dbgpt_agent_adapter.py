import asyncio
import os
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from dbgpt.agent.core.action import BlankAction
from dbgpt.agent.core.agent import AgentContext as DBGPTAgentContext
from dbgpt.agent.core.agent import AgentMessage as DBGPTAgentMessage
from dbgpt.agent.core.base_agent import ConversableAgent, ProfileConfig
from dbgpt.agent.core.memory import AgentMemory as DBGPTAgentMemory
from dbgpt.agent.resource import ToolPack
from dbgpt.agent.resource import tool as dbgpt_tool
from dbgpt.agent.util.llm.llm import LLMConfig
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient

from app.agent.agent.agent_adapter import AgentAdapter
from app.memory.message import AgentMessage
from app.toolkit.tool.tool import Tool


class DBGPTAgentAdapter(AgentAdapter):
    """DB-GPT adapter implementation based on ConversableAgent."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        agent_memory: Optional[DBGPTAgentMemory] = None,
        tool_list: Optional[List[Tool]] = None,
        **kwargs,
    ):
        """Initialize DB-GPT adapter."""
        self.id = str(uuid4())
        self.agent: ConversableAgent = None
        self.llm_config = llm_config
        self.agent_memory = agent_memory or DBGPTAgentMemory()
        self.agent_context = DBGPTAgentContext(
            conv_id=self.id, language="en", temperature=0.7, max_new_tokens=2048
        )
        self.tool_list = tool_list
        self.kwargs = kwargs

    async def init_client(self):
        """Initialize DB-GPT ConversableAgent."""
        # Create ConversableAgent with provided config
        profile = self.kwargs.get("profile_config") or ProfileConfig(
            name=self.kwargs.get("name", "dbgpt_agent"),
            role=self.kwargs.get("role", "assistant"),
            goal=self.kwargs.get("goal", "complete the task"),
            desc=self.kwargs.get("desc", "You are an AI"),
            system_prompt_template=self.kwargs.get(
                "system_prompt_template", "You are an AI"
            ),
        )
        self.kwargs.pop("name", None)

        self.agent = ConversableAgent(
            name=profile.name,
            profile=profile,
            llm_config=self.llm_config,
            memory=self.agent_memory,
            max_retry_count=1,
            is_team=self.kwargs.get("is_team", True),
            stream_out=self.kwargs.get("stream_out", False),
            show_reference=self.kwargs.get("show_reference", False),
            **self.kwargs,
        )
        self.agent._init_actions([BlankAction])

        if not self.llm_config:
            llm_client = OpenAILLMClient(
                model_alias="qwen-turbo",
                api_base=os.getenv("OPENAI_API_BASE"),
                api_key=os.getenv("OPENAI_API_KEY"),
            )
            self.llm_config = LLMConfig(llm_client=llm_client)

        # Bind agent with memory, context and tool pack
        tool_pack = self._init_dbgpt_tool_pack()
        self.agent.bind(self.llm_config).bind(self.agent_memory).bind(
            self.agent_context
        ).bind(tool_pack)

        # Build the agent (initialize components)
        await self.agent.build()

    def _init_dbgpt_tool_pack(self) -> ToolPack:
        """Initialize DB-GPT tool pack. It converts custom tools to DB-GPT compatible tools."""
        if not self.tool_list:
            return ToolPack([])

        dbgpt_tools = []
        for custom_tool in self.tool_list:
            _dbgpt_tool = self._convert_to_dbgpt_tool(custom_tool)
            dbgpt_tools.append(_dbgpt_tool)
        return ToolPack(dbgpt_tools)

    def _convert_to_dbgpt_tool(self, custom_tool: Tool) -> Callable:
        """Convert custom tool to DB-GPT tool."""
        original_function = custom_tool.function
        args_schema = custom_tool.args_schema

        @dbgpt_tool(args_schema=args_schema)
        async def wrapped_function(*args, **kwargs):
            """Wrapped version of the original function.

            If the original function is a synchronous function, call it directly.
            Otherwise, run it by run_sync_in_worker_thread.
            """
            if asyncio.iscoroutinefunction(original_function):
                result = await original_function(*args, **kwargs)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: original_function(*args, **kwargs)
                )

            return result

        # Copy original function's name and docstring
        wrapped_function.__name__ = original_function.__name__
        wrapped_function.__doc__ = original_function.__doc__

        return wrapped_function

    async def receive_message(self, message: AgentMessage) -> AgentMessage:
        """Receive message, process it through DB-GPT agent and return response.

        Args:
            message: The message to process
            role: The role of the message sender

        Returns:
            The response from LLM
        """
        # Convert to DB-GPT message format
        received_message = DBGPTAgentMessage(
            content=message.content,
        )

        # Use DB-GPT's generate_reply to get response
        response: DBGPTAgentMessage = await self.agent.generate_reply(
            received_message=received_message,
            sender=self.agent,  # sender is self.agent as we're asking it to generate
        )

        # Convert response to AgentMessage
        agent_response: AgentMessage = AgentMessage(
            msg_id=str(uuid4()),
            sender_id=message.receiver_id,
            receiver_id=message.sender_id,
            status="success" if response.success else "failed",
            content=response.content,
            timestamp=str(),
        )

        return agent_response

    async def parse_response(self, response: AgentMessage) -> Dict[str, Any]:
        """Parse DB-GPT's response, if needed. For example, extract structured text from response.

        Args:
            response: The response from DB-GPT agent
        """

    async def handle_tool_call(self, tool_calls: List[dict]) -> List[dict]:
        """Handle tool calls using DB-GPT's action system."""

    async def update_memory(self, message: AgentMessage):
        """Update DB-GPT's message history using its memory system."""
