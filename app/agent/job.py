from dataclasses import dataclass, field
from typing import Optional
from uuid import uuid4

from app.commom.system_env import SysEnvKey, SystemEnv
from app.memory.message import WorkflowMessage


@dataclass
class JobExecutionContext:
    """JobExecutionContext is the dataclass including the context of the job."""

    retry_count: int = 0
    max_retries: int = int(SystemEnv.get(SysEnvKey.MAX_RETRIES))


@dataclass
class Job:
    """Job is the dataclass assigned to the leader or the experts.

    Attributes:
        session_id (str): The unique identifier of the session.
        goal (str): The goal of the task.
        id (str): The unique identifier of the task.
        context (str): The context of the task.
        output_schema (str): The output schema of the task.
        response (Optional[WorkflowMessage]): The response of the workflow.
    """

    session_id: str
    goal: str
    context: str = ""
    output_schema: str = "Output schema is not determined."
    id: str = field(default_factory=lambda: str(uuid4()))
    execution_context: JobExecutionContext = field(default_factory=JobExecutionContext)
    response: Optional[WorkflowMessage] = None
