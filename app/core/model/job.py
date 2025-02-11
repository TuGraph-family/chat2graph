from dataclasses import dataclass, field
from uuid import uuid4

from app.core.common.system_env import SystemEnv


@dataclass
class Job:
    """Job is the dataclass assigned to the leader or the experts.

    Attributes:
        id (str): The unique identifier of the job.
        session_id (str): The unique identifier of the session.
        goal (str): The goal of the job.
        context (str): The context of the job.
        life_cycle (int): The life cycle of the job.
    """

    goal: str
    context: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class SubJob(Job):
    """Sub job which is decomposed by the leader.

    Attributes:
        ...
        output_schema (str): The output schema of the sub job.
        life_cycle (int): The life cycle of the sub job.
    """

    output_schema: str = "Output schema is not determined."
    life_cycle: int = SystemEnv.LIFE_CYCLE
