from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Job:
    """Job is the dataclass assigned to the leader or the experts.

    Attributes:
        session_id (str): The unique identifier of the session.
        goal (str): The goal of the task.
        id (str): The unique identifier of the task.
        context (str): The context of the task.
        output_schema (str): The output schema of the task.
    """

    session_id: str
    goal: str
    context: str = ""
    output_schema: str = "Output schema is not determined."
    id: str = field(default_factory=lambda: str(uuid4()))
