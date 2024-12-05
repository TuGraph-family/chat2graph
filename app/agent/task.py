from dataclasses import dataclass
from uuid import uuid4

from app.commom.type import TaskLabel


@dataclass
class Task:
    """Task in the system.e

    Attributes:
        session_id (str): The unique identifier of the session.
        goal (str): The goal of the task.
        id (str): The unique identifier of the task.
        context (str): The context of the task.
        lable (TaskLabel): The lable of the
            task to indicate whether it is decomposed from the original task.
    """

    session_id: str
    goal: str
    id: str = str(uuid4())
    context: str = ""
    lable: TaskLabel = TaskLabel.ORIGINAL

    def get_session_id(self) -> str:
        """Get the unique identifier of the session."""
        return self.session_id

    def get_goal(self) -> str:
        """Get the goal of the task."""
        return self.goal

    def get_id(self) -> str:
        """Get the unique identifier of the task."""
        return self.id

    def get_context(self) -> str:
        """Get the context of the task."""
        return self.context

    def get_lable(self) -> TaskLabel:
        """Get the lable of the task."""
        return self.lable
