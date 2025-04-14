from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4

from app.core.common.system_env import SystemEnv


class JobType(Enum):
    """JobType is the enum class to represent the job type."""

    JOB = "JOB"
    SUB_JOB = "SUB_JOB"


@dataclass
class Job:
    """Job is the dataclass assigned to the leader or the experts.

    Attributes:
        id (str): The unique identifier of the job.
        session_id (str): The unique identifier of the session.
        goal (str): The goal of the job.
        context (str): The context of the job.
        assigned_expert_name (str): The name of the assigned expert determined by the user.
        dag (Optional[str]): The directed acyclic graph (DAG) of the job, which describes the
            dependencies between the sub jobs. It is compressed as a json string.
    """

    goal: str
    context: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid4()))
    assigned_expert_name: Optional[str] = None
    dag: Optional[str] = None

    def __post_init__(self):
        """Post initialization to ensure the id and session_id are set correctly."""
        if not self.context:
            self.context = ""


@dataclass
class SubJob(Job):
    """Sub job which is decomposed by the leader.

    Attributes:
        ...
        original_job_id (str): The id of the parent/orignal job.
        expert_id (str): The id of the expert attached to the sub job.
        output_schema (str): The output schema of the sub job.
        life_cycle (int): The life cycle of the sub job.
        is_legacy (bool): Whether the sub job is legacy, which means the subjob is
            decomposed into sub-subjobs by the leader and the subjob will not be
            executed by the agent anymore.
    """

    original_job_id: Optional[str] = None  # it is required for the sub job
    expert_id: Optional[str] = None  # it is required for the sub job
    output_schema: str = "Output schema is not determined."
    life_cycle: int = SystemEnv.LIFE_CYCLE
    is_legacy: bool = False
    thinking: Optional[str] = None
    dag: None = field(default=None, init=False)

    def __post_init__(self):
        """
        Post initialization to ensure the id and session_id are set correctly.
        For sub jobs, we will not set the assigned_expert_name or dag.
        """
        super().__post_init__()
        if not self.output_schema:
            # ensure output_schema is always a string
            self.output_schema = "Output schema is not determined."
