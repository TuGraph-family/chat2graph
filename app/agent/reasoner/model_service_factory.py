from abc import ABC

from app.agent.reasoner.model_service import ModelService
from app.commom.type import PlatformType
from app.plugin.dbgpt.dbgpt_llm_client import DbgptLlmClient


class ModelServiceFactory(ABC):
    """Model service factory."""

    @classmethod
    def create(cls, platform_type: PlatformType, **kwargs) -> ModelService:
        """Create a model service."""
        if platform_type == PlatformType.DBGPT:
            return DbgptLlmClient()
        # TODO: add more platforms, so the **kwargs can be used to pass the necessary parameters
        raise ValueError(f"Cannot create model service of type {platform_type}")
