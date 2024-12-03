from dataclasses import dataclass
from typing import Optional

from app.system_env import SystemEnv


@dataclass
class ModelConfig:
    """Model configuration."""

    model_name: Optional[str] = SystemEnv.model_name()
    base_url: Optional[str] = SystemEnv.base_url()
    api_key: Optional[str] = SystemEnv.api_key()
    streaming: Optional[bool] = False
