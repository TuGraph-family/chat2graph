import os
import threading
from contextvars import ContextVar
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from app.commom.type import PlatformType

_context_cache: ContextVar[Dict[str, Any]] = ContextVar("env_cache", default={})


class SystemEnv:
    """Singleton class to manage system environment variables"""

    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls) -> "SystemEnv":
        with cls._lock:
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
            cls._initialized = True

    @staticmethod
    def get(key: str, default_value: Optional[str] = None) -> str:
        """Get value following priority: context cache > .env > os env > default value"""
        context_cache = _context_cache.get()
        if key in context_cache:
            return context_cache[key]

        env_value = os.getenv(key)
        if env_value:
            return env_value

        return default_value if default_value else ""

    @staticmethod
    def platform_type() -> PlatformType:
        """Get platform type with caching and enum conversion"""
        platform_name = SystemEnv.get("PLATFORM_TYPE", PlatformType.DBGPT.name)
        return PlatformType[platform_name]
