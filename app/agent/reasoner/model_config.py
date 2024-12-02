import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelConfig:
    """Model configuration."""

    model_alias: str
    api_base: Optional[str] = os.getenv("QWEN_API_BASE")
    api_key: Optional[str] = os.getenv("QWEN_API_KEY")
    streaming: Optional[bool] = False
