import time
from typing import List

from dbgpt.core import (  # type: ignore
    AIMessage,
    HumanMessage,
    ModelMessage,
    ModelRequest,
    SystemMessage,
)
from dbgpt.model.proxy.base import LLMClient  # type: ignore
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient  # type: ignore

from app.agent.reasoner.model_service import ModelService
from app.commom.system_env import SystemEnv
from app.memory.message import AgentMessage


class DbgptLlmClient(ModelService):
    """DBGPT LLM Client.

    Attributes:
        _sys_prompt_template (str): The system prompt template.
        _sys_prompt (str): The system prompt.
        _llm_client (LLMClient): The LLM client provided by DB-GPT.
    """

    def __init__(self, sys_prompt_template: str):
        super().__init__()
        self._sys_prompt_template: str = sys_prompt_template
        self._sys_prompt: str = ""

        # use openai llm client by default
        # TODO: support other llm clients
        self._llm_client: LLMClient = OpenAILLMClient(
            model_alias=SystemEnv.get("PROXYLLM_BACKEND", "gpt-4o-mini"),
            api_base=SystemEnv.get("PROXY_SERVER_URL"),
            api_key=SystemEnv.get("PROXY_API_KEY"),
        )

    async def generate(self, messages: List[AgentMessage]) -> AgentMessage:
        """Generate a text given a prompt."""
        if len(messages) == 0:
            raise ValueError("No messages provided.")
        sys_message = SystemMessage(content=self._sys_prompt)
        base_messages: List[AIMessage] = [sys_message]

        for message in messages:
            if message.sender == "Actor":
                base_messages.append(AIMessage(content=message.content))
            else:
                base_messages.append(HumanMessage(content=message.content))

        model_messages = ModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=SystemEnv.get("PROXYLLM_BACKEND", "gpt-4o-mini"),
            messages=model_messages,
        )
        model_output = await self._llm_client.generate(model_request)
        sender = "Actor" if messages[-1].sender == "Thinker" else "Thinker"
        response = AgentMessage(
            sender=sender,
            content=model_output.text,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        return response

    def set_sys_prompt(self, task: str) -> None:
        """Set the system prompt."""
        self._sys_prompt = self._sys_prompt_template.format(task=task)
