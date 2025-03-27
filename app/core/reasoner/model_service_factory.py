from app.core.common.type import ModelPlatformType
from app.core.reasoner.model_service import ModelService
from app.plugin.aisuite.aisuite_llm_client import AiSuiteLlmClient
from app.plugin.dbgpt.dbgpt_llm_client import DbgptLlmClient


class ModelServiceFactory:
    """Model service factory."""

    @classmethod
    def create(cls, model_platform_type: ModelPlatformType, **kwargs) -> ModelService:
        """Create a model service."""
        if model_platform_type == ModelPlatformType.DBGPT:
            return DbgptLlmClient()
        if model_platform_type == ModelPlatformType.AISUITE:
            return AiSuiteLlmClient()
        # TODO: add more platforms, so the **kwargs can be used to pass the necessary parameters
        raise ValueError(f"Cannot create model service of type {model_platform_type}")
