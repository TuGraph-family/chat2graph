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

from app.agent.reasoner.model_config import ModelConfig
from app.agent.reasoner.model_service import ModelService
from app.memory.message import AgentMessage


class DbgptLlmClient(ModelService):
    """DBGPT LLM Client.

    Attributes:
        _model_name (str): The model name.
        _streaming (bool): The streaming flag.
        _sys_prompt (str): The system prompt.
        _llm_client (LLMClient): The LLM client provided by DB-GPT.
    """

    def __init__(self, sys_prompt: str, model_config: ModelConfig):
        super().__init__()
        self._model_name = model_config.model_name
        self._streaming = model_config.streaming
        self._sys_prompt = sys_prompt

        base_url = model_config.base_url
        api_key = model_config.api_key

        # use openai llm client by default
        self._llm_client: LLMClient = OpenAILLMClient(
            model_alias=self._model_name,
            api_base=base_url,
            api_key=api_key,
            streaming=self._streaming,
        )

    async def generate(self, messages: List[AgentMessage]) -> AgentMessage:
        """Generate a text given a prompt."""
        if self._streaming:
            raise ValueError("The streaming output is not supported yet.")
        if len(messages) == 0:
            raise ValueError("No messages provided.")
        sys_message = SystemMessage(content=self._sys_prompt)
        base_messages: List[AIMessage] = [sys_message]

        n = len(messages)
        for i, message in enumerate(messages):
            if (i + n) % 2 == 0:
                base_messages.append(AIMessage(content=message.content))
            else:
                base_messages.append(HumanMessage(content=message.content))

        model_messages = ModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=self._model_name, messages=model_messages
        )
        model_output = await self._llm_client.generate(model_request)
        response = AgentMessage(
            sender_id=messages[-1].receiver_id,
            receiver_id=messages[-1].sender_id,
            content=model_output.text,
            status="successed",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            reasoning_id=messages[-1].reasoning_id,
        )

        return response

    def set_sys_prompt(self, task: str) -> None:
        """Set the system prompt."""
        self._sys_prompt = self._sys_prompt.format(task=task)
