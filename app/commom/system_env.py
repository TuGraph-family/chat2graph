import os
import threading
from contextvars import ContextVar
from enum import Enum, unique
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from app.commom.type import PlatformType

_context_cache: ContextVar[Dict[str, Any]] = ContextVar("env_cache", default={})


@unique
class SysEnvKey(str, Enum):
    """System environment variable keys.

    Attributes:
        PLATFORM_TYPE: The type of platform
        PROXYLLM_BACKEND: The backend of ProxLLM
        PROXY_SERVER_URL: The URL of the proxy server
        PROXY_API_KEY: The API key of the proxy server
        REASONING_ROUNDS: The rounds of reasoning in the reasoner
    """

    PLATFORM_TYPE = "PLATFORM_TYPE"
    PROXYLLM_BACKEND = "PROXYLLM_BACKEND"
    PROXY_SERVER_URL = "PROXY_SERVER_URL"
    PROXY_API_KEY = "PROXY_API_KEY"
    REASONING_ROUNDS = "REASONING_ROUNDS"

    def get_default(self) -> Optional[str]:
        """Get default value for the key."""
        defaults = {
            self.PLATFORM_TYPE: PlatformType.DBGPT.name,
            self.PROXYLLM_BACKEND: "gpt-4o-mini",
            self.PROXY_SERVER_URL: None,
            self.PROXY_API_KEY: None,
            self.REASONING_ROUNDS: "5",
        }
        return defaults.get(self)


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

        if not default_value:
            # try to get default from SysEnvKey if it exists
            try:
                sys_key = SysEnvKey(key)
                key_default = sys_key.get_default()
                if key_default is not None:
                    return key_default
                else:
                    return ""
            except ValueError:
                return ""  # Key is not in SysEnvKey enum

        return default_value

    @staticmethod
    def platform_type() -> PlatformType:
        """Get platform type with caching and enum conversion"""
        platform_name = SystemEnv.get(SysEnvKey.PLATFORM_TYPE)
        return PlatformType[platform_name]
