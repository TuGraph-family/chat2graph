from abc import ABC

from app.agent.reasoner.model_service import ModelService
from app.plugin.dbgpt.dbgpt_llm_client import DbgptLlmClient
from app.commom.type import PlatformType


class ModelServiceFactory(ABC):
    """Model service factory."""

    @classmethod
    def create(cls, platform_type: PlatformType, **kwargs) -> ModelService:
        """Create a model service."""
        if platform_type == PlatformType.DBGPT:
            sys_prompt_template = (
                kwargs.get("sys_prompt_template")
                or "You are a helpful assistant.\nYour task:\n{task}"
            )
            return DbgptLlmClient(sys_prompt_template=sys_prompt_template)
        raise ValueError(f"Cannot create model service of type {platform_type}")
