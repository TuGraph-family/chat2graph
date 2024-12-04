from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.memory.memory import Memory
from app.toolkit.tool.tool import Tool


class ReasonerCaller(ABC):
    """Reasoner caller."""

    def __init__(
        self,
        system_id: str,
        session_id: str,
        task_id: str,
        agent_id: str,
        operator_id: str,
    ):
        self._system_id: str = system_id
        self._session_id: str = session_id
        self._task_id: str = task_id
        self._agent_id: str = agent_id
        self._operator_id: str = operator_id

    def get_system_id(self) -> str:
        """Get the system id."""
        return self._system_id

    def get_session_id(self) -> str:
        """Get the session id."""
        return self._session_id

    def get_task_id(self) -> str:
        """Get the task id."""
        return self._task_id

    def get_agent_id(self) -> str:
        """Get the agent id."""
        return self._agent_id

    def get_operator_id(self) -> str:
        """Get the operator id."""
        return self._operator_id


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
