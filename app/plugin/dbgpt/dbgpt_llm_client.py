import time
from typing import List, Literal

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
from app.commom.system_env import SystemEnv
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
            model_alias=SystemEnv.get("PROXYLLM_BACKEND", "gpt-4o-mini"),
            api_base=SystemEnv.get("PROXY_SERVER_URL"),
            api_key=SystemEnv.get("PROXY_API_KEY"),
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

        # generate response using the llm client
        model_output = await self._llm_client.generate(model_request)

        # convert the model output to agent message
        sender: Literal["Thinker", "Actor", "Reasoner"]
        if messages[-1].sender == "Thinker":
            sender = "Actor"
        elif messages[-1].sender == "Actor":
            sender = "Thinker"
        else:
            sender = "Reasoner"
        response = AgentMessage(
            sender=sender,
            content=model_output.text,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        # log the response if enabled
        print_messages = SystemEnv.get("PRINT_MESSAGES", "True").lower() == "true"
        if print_messages:
            if sender == "Thinker":
                print(f"\033[94mThinker:\n{response.content}\033[0m\n")
            elif sender == "Actor":
                print(f"\033[92mActor:\n{response.content}\033[0m\n")
            else:
                print(f"\033[93mReasoner:\n{response.content}\033[0m\n")

        return response
