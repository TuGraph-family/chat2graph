from enum import Enum


class PlatformType(Enum):
    """Model type enum."""

    DBGPT = "dbgpt"


class ReasonerType(Enum):
    """Reasoner type enum."""

    MONO = "mono"
    DUAL = "dual"


class MessageSourceType(Enum):
    """Message source type enum."""

    THINKER = "Thinker"
    ACTOR = "Actor"
    MODEL = "Model"


class InsightType(Enum):
    """Insight Type"""

    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"


class WorkflowStatus(Enum):
    """WorkflowStatus defines the execution status which is evaluated by the eval_operator."""

    SUCCESS = "success"
    EXECUTION_ERROR = "execution_error"
    INPUT_DATA_ERROR = "input_data_error"
    JOB_TOO_COMPLICATED_ERROR = "job_too_complicated_error"
    MAX_RETRIES_REACHED = "max_retries_reached"


class JobStatus(Enum):
    """Job status type."""

    CREATED = "created"
    RUNNING = "running"
    FINISHED = "finished"
    FAILED = "failed"
    STOPPED = "stopped"
