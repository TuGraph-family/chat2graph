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


class TaskLabel(Enum):
    """Task label enum. The lable of the task to indicate
    whether it is decomposed from the original task
    """

    ORIGINAL = "original"
    GENERATED = "generated"
