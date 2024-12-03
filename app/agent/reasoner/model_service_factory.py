from abc import ABC

from app.agent.reasoner.model_config import ModelConfig
from app.agent.reasoner.model_service import ModelService
from app.plugin.dbgpt.dbgpt_llm_client import DbgptLlmClient
from app.type import PlatformType


class ModelServiceFactory(ABC):
    """Model service factory."""

    @classmethod
    def create(
        cls, platform_type: PlatformType, model_config: ModelConfig, **kwargs
    ) -> ModelService:
        """Create a model service."""
        if platform_type == PlatformType.DBGPT:
            sys_prompt = kwargs.get("sys_prompt") or "You are a helpful assistant."
            return DbgptLlmClient(sys_prompt=sys_prompt, model_config=model_config)
        raise ValueError(f"Cannot create model service of type {platform_type}")
