from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.memory.memory import Memory
from app.toolkit.tool.tool import Tool


class ReasonerCaller(ABC):
    """Reasoner caller.

    Attributes:
        _system_id: The system id.
        _session_id: The session id.
        _task_id: The task id.
        _agent_id: The agent id.
        _operator_id: The operator id.
    """

    def __init__(self):
        self._system_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._task_id: Optional[str] = None
        self._agent_id: Optional[str] = None
        self._operator_id: Optional[str] = None

    @abstractmethod
    def get_system_id(self) -> str:
        """Get the system id."""

    @abstractmethod
    def get_session_id(self) -> str:
        """Get the session id."""

    @abstractmethod
    def get_task_id(self) -> str:
        """Get the task id."""

    @abstractmethod
    def get_agent_id(self) -> str:
        """Get the agent id."""

    @abstractmethod
    def get_operator_id(self) -> str:
        """Get the operator id."""


class Reasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    @abstractmethod
    async def infer(
        self,
        input: str,
        tools: Optional[List[Tool]] = None,
        caller: Optional[ReasonerCaller] = None,
    ) -> str:
        """Infer by the reasoner."""

    @abstractmethod
    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    @abstractmethod
    async def conclure(self, memory: Memory) -> str:
        """Conclure the inference results."""
