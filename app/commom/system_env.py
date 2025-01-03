import os
from contextvars import ContextVar
from enum import Enum, unique
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

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
    TEMPERATURE = "TEMPERATURE"
    REASONING_ROUNDS = "REASONING_ROUNDS"
    PRINT_REASONER_MESSAGES = "PRINT_REASONER_MESSAGES"

    def get_default(self) -> Optional[str]:
        """Get default value for the key."""
        defaults = {
            self.PLATFORM_TYPE: PlatformType.DBGPT.name,
            self.PROXYLLM_BACKEND: "gpt-4o-mini",
            self.PROXY_SERVER_URL: None,
            self.PROXY_API_KEY: None,
            self.TEMPERATURE: "0.7",
            self.REASONING_ROUNDS: "20",
            self.PRINT_REASONER_MESSAGES: "True",
        }
        return defaults.get(self)


class SystemEnvMeta(type):
    """Singleton class to manage system environment variables"""

    def __init__(cls, name: str, bases: Tuple, dct: Dict):
        super().__init__(name, bases, dct)
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path, override=True)

    def __getattr__(cls, name: str) -> str:
        """Get value following priority: context cache > .env > os env > default value"""
        key = name.upper()

        context_cache = _context_cache.get()
        if key in context_cache:
            return context_cache[key]

        env_value = os.getenv(key)
        if env_value:
            return env_value

        # try to get default from SysEnvKey if it exists
        try:
            sys_key = SysEnvKey(key)
            key_default = sys_key.get_default()
            if key_default is not None:
                return key_default
            else:
                raise AttributeError(f"Key {key} not found in system environment")

        except ValueError:
            raise AttributeError(f"Key {key} not found in system environment")


class SystemEnv(metaclass=SystemEnvMeta):
    """Static class to manage system environment variables"""
