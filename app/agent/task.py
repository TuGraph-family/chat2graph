from dataclasses import dataclass
from typing import Literal
from uuid import uuid4


@dataclass
class Task:
    """Task in the system.e

    Attributes:
        session_id (str): The unique identifier of the session.
        goal (str): The goal of the task.
        id (str): The unique identifier of the task.
        context (str): The context of the task.
        lable (Literal["original", "generated"]): The lable of the
            task to indicate whether it is decomposed from the original task.
    """

    session_id: str
    goal: str
    id: str = str(uuid4())
    context: str = ""
    lable: Literal["original", "generated"] = "original"
