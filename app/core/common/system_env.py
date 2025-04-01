import os
from pathlib import Path
from typing import Any, Dict, Tuple, Type

from dotenv import load_dotenv

from app.core.common.type import (
    KnowledgeStoreType,
    ModelPlatformType,
    WorkflowPlatformType,
)

# system environment variable keys
_env_vars: Dict[str, Tuple[Type, Any]] = {
    "WORKFLOW_PLATFORM_TYPE": (WorkflowPlatformType, WorkflowPlatformType.DBGPT),
    "MODEL_PLATFORM_TYPE": (ModelPlatformType, ModelPlatformType.DBGPT),
    "PROXYLLM_BACKEND": (str, "gpt-4o-mini"),
    "PROXY_SERVER_URL": (str, None),
    "PROXY_API_KEY": (str, None),
    "TEMPERATURE": (float, 0.7),
    "REASONING_ROUNDS": (int, 20),
    "PRINT_REASONER_MESSAGES": (bool, True),
    "PRINT_SYSTEM_PROMPT": (bool, True),
    "PRINT_REASONER_OUTPUT": (bool, True),
    "LIFE_CYCLE": (int, 3),
    "MAX_RETRY_COUNT": (int, 3),
    "DATABASE_URL": (str, f"sqlite:///{os.path.expanduser('~')}/.chat2graph/system/chat2graph.db"),
    "DATABASE_POOL_SIZE": (int, 50),
    "DATABASE_MAX_OVERFLOW": (int, 50),
    "DATABASE_POOL_TIMEOUT": (int, 60),
    "DATABASE_POOL_RECYCLE": (int, 3600),
    "DATABASE_POOL_PRE_PING": (bool, True),
    "APP_ROOT": (str, f"{os.path.expanduser('~')}/.chat2graph"),
    "SCHEMA_FILE_ID": (str, "schema_file_id"),
    "SYSTEM_PATH": (str, "/system"),
    "FILE_PATH": (str, "/files"),
    "KNOWLEDGE_STORE_PATH": (str, "/knowledge_bases"),
    "EMBEDDING_MODEL_NAME": (str, "text-embedding-3-small"),
    "EMBEDDING_MODEL_API_URL": (str, None),
    "EMBEDDING_API_KEY": (str, None),
    "GLOBAL_KNOWLEDGE_BASE_NAME": (str, "Global Knowledge Base"),
    "KNOWLEDGE_STORE_TYPE": (KnowledgeStoreType, KnowledgeStoreType.VECTOR),
    "TUGRAPH_NAME_PREFIX": (str, "Tu_"),
    "GRAPH_KNOWLEDGE_STORE_USERNAME": (str, "admin"),
    "GRAPH_KNOWLEDGE_STORE_PASSWORD": (str, "73@TuGraph"),
    "GRAPH_KNOWLEDGE_STORE_HOST": (str, "127.0.0.1"),
    "GRAPH_KNOWLEDGE_STORE_PORT": (str, "7687"),
    "GRAPH_DB_HOST": (str, "localhost"),
    "GRAPH_DB_PORT": (int, 7687),
    "GRAPH_DB_USERNAME": (str, None),
    "GRAPH_DB_PASSWORD": (str, None),
    "GRAPH_DB_NAME": (str, None),
}

# system environment variable value cache.
_env_values: Dict[str, Any] = {}


class SystemEnvMeta(type):
    """Singleton class to manage system environment variables"""

    def __init__(cls, name: str, bases: Tuple, dct: Dict):
        super().__init__(name, bases, dct)
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path, override=True)

    def __getattr__(cls, name: str) -> Any:
        """Get value following priority: .env > os env > default value"""
        key = name.upper()

        # get value from .env
        val = _env_values.get(key, None)
        if val:
            return val

        # get value from system env
        val = os.getenv(key, None)

        # get key declaration
        (key_type, default_value) = _env_vars.get(key, (None, None))
        if not key_type:
            _env_values[key] = val
            return val

        # use default value
        val = val if val else default_value

        # cast value by type
        if key_type is bool:
            val = str(val).lower() in ("true", "1", "yes") if val else None
        else:
            val = key_type(val) if val else None
        _env_values[key] = val
        return val

    def __setattr__(cls, name: str, value: Any) -> None:
        """Set environment variable value in _env_values cache"""
        key = name.upper()

        # check if key is a valid environment variable
        key_info = _env_vars.get(key, None)
        if key_info:
            key_type, _ = key_info

            # Apply type conversion
            if key_type is bool:
                value = str(value).lower() in ("true", "1", "yes") if value else False
            else:
                value = key_type(value) if value is not None else None

            # store value in cache
            _env_values[key] = value
        else:
            raise AttributeError(f"Invalid environment variable: {name}")


class SystemEnv(metaclass=SystemEnvMeta):
    """Static class to manage system environment variables"""
