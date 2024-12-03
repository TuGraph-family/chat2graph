import os
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from app.agent.reasoner.model_name import ModelName
from app.type import PlatformType

_context_cache: ContextVar[Dict[str, Any]] = ContextVar("env_cache", default={})
# store .env variables separately
_env_cache: Dict[str, str] = {}


class SystemEnv:
    """Singleton class to manage system environment variables"""

    _instance = None
    _initialized = False

    def __new__(cls) -> "SystemEnv":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_env()
        return cls._instance

    @classmethod
    def _load_env(cls):
        """Load .env file once at initialization

        Store values in _env_cache for priority handling
        """
        if not cls._initialized:
            env_path = Path(".env")
            if env_path.exists():
                load_dotenv(env_path)
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            key, value = line.strip().split("=", 1)
                            _env_cache[key.strip()] = value.strip()
            cls._initialized = True

    @property
    def context_cache(self) -> Dict[str, str]:
        """Access to current context cache"""
        return _context_cache.get()

    @staticmethod
    def get(key: str, default_value: Optional[str] = None) -> str:
        """Get value following priority: context cache > .env > os env > default value"""
        SystemEnv._load_env()

        context_cache = _context_cache.get()
        if key in context_cache:
            return context_cache[key]

        if key in _env_cache:
            return _env_cache[key]

        env_value = os.getenv(key)
        if env_value:
            return env_value

        return default_value if default_value else ""

    @staticmethod
    def platform_type() -> PlatformType:
        """Get platform type with caching and enum conversion"""
        platform_name = SystemEnv.get("PLATFORM_TYPE", PlatformType.DBGPT.name)
        return PlatformType[platform_name]

    @staticmethod
    def model_name() -> str:
        """Get model name with caching"""
        return SystemEnv.get("MODEL_NAME", ModelName.QWEN_TURBO.value)

    @staticmethod
    def base_url() -> str:
        """Get base URL with caching"""
        return SystemEnv.get(
            "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    @staticmethod
    def api_key() -> str:
        """Get API key with caching"""
        return SystemEnv.get("QWEN_API_KEY")
