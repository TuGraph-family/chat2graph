from enum import Enum


class ModelName(Enum):
    """Model name."""

    QWEN_MAX = "qwen-max"
    QWEN_TURBO = "qwen-turbo"
    QWEN_PLUS = "qwen-plus"

    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
