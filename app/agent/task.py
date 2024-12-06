from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Task:
    """Task in the system.

    Attributes:
        _session_id (str): The unique identifier of the session.
        _goal (str): The goal of the task.
        _id (str): The unique identifier of the task.
        _context (str): The context of the task.
    """

    def __init__(
        self,
        session_id: str,
        goal: str,
        id: str = str(uuid4()),
        context: str = "",
    ):
        self._session_id = session_id
        self._goal = goal
        self._id = id
        self._context = context

    def get_session_id(self) -> str:
        """Get the unique identifier of the session."""
        return self._session_id

    def get_goal(self) -> str:
        """Get the goal of the task."""
        return self._goal

    def get_id(self) -> str:
        """Get the unique identifier of the task."""
        return self._id

    def get_context(self) -> str:
        """Get the context of the task."""
        return self._context
