from enum import Enum


class PlatformType(Enum):
    """Model type enum."""

    DBGPT = "DBGPT"


class ReasonerType(Enum):
    """Reasoner type enum."""

    MONO = "MONO"
    DUAL = "DUAL"


class MessageSourceType(Enum):
    """Message source type enum."""

    THINKER = "THINKER"
    ACTOR = "ACTOR"
    MODEL = "MODEL"


class ChatMessageRole(Enum):
    """Chat message role enum."""

    USER = "USER"
    SYSTEM = "SYSTEM"


class ChatMessageType(Enum):
    """Chat message type enum."""

    TEXT = "TEXT"
    FILE = "FILE"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


class InsightType(Enum):
    """Insight Type"""

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    TABLE = "TABLE"


class WorkflowStatus(Enum):
    """WorkflowStatus defines the execution status which is evaluated by the eval_operator."""

    SUCCESS = "SUCCESS"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    INPUT_DATA_ERROR = "INPUT_DATA_ERROR"
    JOB_TOO_COMPLICATED_ERROR = "JOB_TOO_COMPLICATED_ERROR"
    MAX_RETRIES_REACHED = "MAX_RETRIES_REACHED"


class JobStatus(Enum):
    """Job status type."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class KnowledgeStoreType(Enum):
    """Knowledge store type."""

    VECTOR = "VECTOR"
    GRAPH = "GRAPH"


class KnowledgeStoreCategory(Enum):
    """Knowledge store category."""

    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"


class KnowledgeStoreFileStatus(Enum):
    """Knowledge store file status."""

    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"


class FileStorageType(Enum):
    """File storage type."""

    LOCAL = "LOCAL"
