import os
from pathlib import Path
from typing import Any, Dict, Tuple, Type

from dotenv import load_dotenv

from app.core.common.type import (
    GraphDbType,
    KnowledgeStoreType,
    ModelPlatformType,
    WorkflowPlatformType,
)

# system environment variable keys
_env_vars: Dict[str, Tuple[Type, Any]] = {
    "WORKFLOW_PLATFORM_TYPE": (WorkflowPlatformType, WorkflowPlatformType.DBGPT),
    "MODEL_PLATFORM_TYPE": (ModelPlatformType, ModelPlatformType.LITELLM),
    "LLM_NAME": (str, None),
    "LLM_ENDPOINT": (str, None),
    "LLM_APIKEY": (str, None),
    "TEMPERATURE": (float, 0.7),
    "MAX_TOKENS": (int, 1048576),
    "MAX_COMPLETION_TOKENS": (int, 65535),
    "MAX_REASONING_ROUNDS": (int, 20),
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
    "SYSTEM_PATH": (str, "/system"),
    "FILE_PATH": (str, "/files"),
    "KNOWLEDGE_STORE_PATH": (str, "/knowledge_bases"),
    "EMBEDDING_MODEL_NAME": (str, "Qwen/Qwen3-Embedding-4B"),
    "EMBEDDING_MODEL_ENDPOINT": (str, "https://api.siliconflow.cn/v1/embeddings"),
    "EMBEDDING_MODEL_APIKEY": (str, None),
    "GLOBAL_KNOWLEDGE_BASE_NAME": (str, "Global Knowledge Base"),
    "KNOWLEDGE_STORE_TYPE": (KnowledgeStoreType, KnowledgeStoreType.VECTOR),
    "TUGRAPH_NAME_PREFIX": (str, "Tu_"),
    "GRAPH_KNOWLEDGE_STORE_USERNAME": (str, "admin"),
    "GRAPH_KNOWLEDGE_STORE_PASSWORD": (str, "73@TuGraph"),
    "GRAPH_KNOWLEDGE_STORE_HOST": (str, "127.0.0.1"),
    "GRAPH_KNOWLEDGE_STORE_PORT": (int, 17687),
    "GRAPH_DB_TYPE": (GraphDbType, GraphDbType.NEO4J),
    "GRAPH_DB_HOST": (str, "localhost"),
    "GRAPH_DB_PORT": (int, 7687),
    "GRAPH_DB_USERNAME": (str, None),
    "GRAPH_DB_PASSWORD": (str, None),
    "GRAPH_DB_NAME": (str, "Default Graph DB"),
    "SCHEMA_FILE_NAME": (str, "graph.db.schema.json"),
    "SCHEMA_FILE_ID": (str, "schema_file_id"),
    "LANGUAGE": (str, "en-US"),
    "ENABLE_MEMFUSE": (bool, False),  # enable MemFuse as agent memory module
    "PRINT_MEMORY_LOG": (bool, False),
    "MEMFUSE_BASE_URL": (str, "http://localhost:8765"),
    "MEMFUSE_API_KEY": (str, None),
    "MEMFUSE_TIMEOUT": (float, 30.0),
    "MEMFUSE_RETRY_COUNT": (int, 3),
    "MEMFUSE_RETRIEVAL_TOP_K": (int, 5),
    "MEMFUSE_MAX_CONTENT_LENGTH": (int, 10000),
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
        if val is not None:
            return val

        # get value from system env
        val = os.getenv(key, None)

        # get key declaration
        (key_type, default_value) = _env_vars.get(key, (None, None))
        if not key_type:
            _env_values[key] = val
            return val

        # use default value
        # only fall back to default when the env var is truly missing (None)
        val = default_value if val is None else val

        # cast value by type
        if key_type is bool:
            val = (str(val).lower() in ("true", "1", "yes")) if val is not None else None
        else:
            val = key_type(val) if val is not None else None

        _env_values[key] = val
        return val

    def __setattr__(cls, name: str, value: Any) -> None:
        """Set environment variable value in _env_values cache"""
        key = name.upper()

        # check if key is a valid environment variable
        key_info = _env_vars.get(key, None)
        if key_info:
            key_type, _ = key_info

            # apply type conversion
            if key_type is bool:
                value = str(value).lower() in ("true", "1", "yes") if value else False
            else:
                value = key_type(value) if value else None

            # store value in cache
            _env_values[key] = value
        else:
            raise AttributeError(f"Invalid environment variable: {name}")


class SystemEnv(metaclass=SystemEnvMeta):
    """Static class to manage system environment variables"""
