from enum import Enum


class PlatformType(Enum):
    """Model type enum."""

    DBGPT = "dbgpt"


class MessageSourceType(Enum):
    """Message source type enum."""

    THINKER = "Thinker"
    ACTOR = "Actor"
    MODEL = "Model"
    USER = "User"
