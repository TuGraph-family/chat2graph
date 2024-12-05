import time
from typing import List

from dbgpt.core import (  # type: ignore
    AIMessage,
    BaseMessage,
    HumanMessage,
    ModelMessage,
    ModelRequest,
    SystemMessage,
)
from dbgpt.model.proxy.base import LLMClient  # type: ignore
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient  # type: ignore

from app.agent.reasoner.model_service import ModelService
from app.commom.system_env import SysEnvKey, SystemEnv
from app.commom.type import MessageSourceType
from app.memory.message import AgentMessage


class DbgptLlmClient(ModelService):
    """DBGPT LLM Client.

    Attributes:
        _llm_client (LLMClient): The LLM client provided by DB-GPT.
    """

    def __init__(self):
        super().__init__()
        # use openai llm client by default
        # TODO: Support other llm clients
        self._llm_client: LLMClient = OpenAILLMClient(
            model_alias=SystemEnv.get(SysEnvKey.PROXYLLM_BACKEND),
            api_base=SystemEnv.get(SysEnvKey.PROXY_SERVER_URL),
            api_key=SystemEnv.get(SysEnvKey.PROXY_API_KEY),
        )

    async def generate(
        self, sys_prompt: str, messages: List[AgentMessage]
    ) -> AgentMessage:
        """Generate a text given a prompt."""
        if len(messages) == 0:
            raise ValueError("No messages provided.")

        # convert system prompt to system message
        sys_message = SystemMessage(content=sys_prompt)
        base_messages: List[BaseMessage] = [sys_message]

        # convert the conversation messages for LLM
        # thinker <-> human, actor <-> ai
        for message in messages:
            if message.get_source_type() == MessageSourceType.ACTOR:
                base_messages.append(AIMessage(content=message.get_payload()))
            else:
                base_messages.append(HumanMessage(content=message.get_payload()))
        model_messages = ModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=SystemEnv.get(SysEnvKey.PROXYLLM_BACKEND),
            messages=model_messages,
        )

        # generate response using the llm client
        model_output = await self._llm_client.generate(model_request)

        # convert the model output to agent message
        response = AgentMessage(
            content=model_output.text,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        return response
