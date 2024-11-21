import os
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List
from uuid import uuid4

from dbgpt.core import (
    AIMessage,
    HumanMessage,
    ModelMessage,
    ModelRequest,
    SystemMessage,
)
from dbgpt.model.proxy.base import LLMClient
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient

from app.memory.message import AgentMessage


class ModelService(ABC):
    """Model service."""

    def __init__(self):
        self.id = str(uuid4())

    @abstractmethod
    async def generate(self, messages: List[AgentMessage]) -> AgentMessage:
        """Generate a text given a prompt (non-)streaming"""

    @abstractmethod
    def set_sys_prompt(self, task: str) -> None:
        """Set the system prompt."""


class DbgptLllmClient(ModelService):
    """DBGPT LLM service."""

    def __init__(self, sys_prompt: str, model_config: Dict[str, Any]):
        super().__init__()
        self.model_alias = model_config.get("model_alias") or "qwen-turbo"
        api_base = model_config.get("api_base") or os.getenv("QWEN_API_BASE")
        api_key = model_config.get("api_key") or os.getenv("QWEN_API_KEY")
        self.streaming = model_config.get("streaming") or False

        self.sys_prompt = sys_prompt

        # use openai llm client by default
        self._llm_client: LLMClient = OpenAILLMClient(
            model_alias=self.model_alias,
            api_base=api_base,
            api_key=api_key,
            streaming=self.streaming,
        )

    async def generate(self, messages: List[AgentMessage]) -> AgentMessage:
        """Generate a text given a prompt."""
        if self.streaming:
            raise ValueError("The streaming output is not supported yet.")
        if len(messages) == 0:
            raise ValueError("No messages provided.")
        sys_message = SystemMessage(content=self.sys_prompt)
        base_messages: List[AIMessage] = [sys_message]

        n = len(messages)
        for i, message in enumerate(messages):
            if (i + n) % 2 == 0:
                base_messages.append(AIMessage(content=message.content))
            else:
                base_messages.append(HumanMessage(content=message.content))

        model_messages = ModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=self.model_alias, messages=model_messages
        )
        model_output = await self._llm_client.generate(model_request)
        response = AgentMessage(
            sender_id=messages[-1].receiver_id,
            receiver_id=messages[-1].sender_id,
            content=model_output.text,
            status="successed",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            op_id=messages[-1].op_id,
        )

        return response

    def set_sys_prompt(self, task: str) -> None:
        """Set the system prompt."""
        self.sys_prompt = self.sys_prompt.format(task=task)


class ModelType(Enum):
    """Model type enum."""

    DBGPT = "dbgpt"


class ModelServiceFactory(ABC):
    """Model service factory."""

    @classmethod
    def create(
        cls, model_type: ModelType, model_config: Dict[str, Any], **kwargs
    ) -> ModelService:
        """Create a model service."""
        if model_type == ModelType.DBGPT:
            sys_prompt = kwargs.get("sys_prompt") or "You are a helpful assistant."
            return DbgptLllmClient(sys_prompt=sys_prompt, model_config=model_config)
        raise ValueError(f"Cannot create model service of type {model_type}")
