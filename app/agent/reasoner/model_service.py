import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from uuid import uuid4

from dbgpt.core import BaseMessage, ModelMessage, ModelRequest
from dbgpt.model.proxy.base import LLMClient
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient

from app.memory.message import AgentMessage


class ModelService(ABC):
    """Model service."""

    def __init__(self):
        self.id = str(uuid4())

    @abstractmethod
    async def generate(self, messages: List[AgentMessage]) -> str:
        """Generate a text given a prompt (non-)streaming"""


class DbgptLllmClient(ModelService):
    """DBGPT LLM service."""

    def __init__(self, model_config: Dict[str, Any]):
        super().__init__()
        self.model_alias = model_config.get("model_alias") or "qwen-turbo"
        api_base = model_config.get("api_base") or os.getenv("QWEN_API_BASE")
        api_key = model_config.get("api_key") or os.getenv("QWEN_API_KEY")
        self.streaming = model_config.get("streaming") or False

        # use openai llm client by default
        self._llm_client: LLMClient = OpenAILLMClient(
            model_alias=self.model_alias,
            api_base=api_base,
            api_key=api_key,
            streaming=self.streaming,
        )

    async def generate(self, messages: List[AgentMessage]) -> str:
        """Generate a text given a prompt."""
        if self.streaming:
            raise ValueError("The streaming output is not supported yet.")
        base_messages: List[BaseMessage] = [
            BaseMessage(content=msg.content) for msg in messages
        ]
        model_messages = ModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=self.model_alias, messages=model_messages
        )

        return await self._llm_client.generate(model_request)


class ModelServiceFactory(ABC):
    @classmethod
    def create(
        cls, model_type: str, model_config: Dict[str, Any], **kwargs
    ) -> ModelService:
        """Create a model service."""
        if model_type == "dbgpt":
            return DbgptLllmClient(model_config)
        raise ValueError(f"Cannot create model service of type {model_type}")
