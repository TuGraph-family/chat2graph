from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional
from uuid import uuid4

from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.workflow import Workflow
from app.core.model.message import AgentMessage


@dataclass
class Profile:
    """Profile of the agent.

    Attributes:
        name (str): The name of the agent.
        description (str): The description of the agent.
    """

    name: str
    description: str = ""


@dataclass
class AgentConfig:
    """Configuration for the base agent.

    Attributes:
        profile (Profile): The profile of the agent.
        reasoner (Reasoner): The reasoner of the agent.
        workflow (Optional[Workflow]): The workflow of the agent.
    """

    # TODO: to be refactored (by yaml)
    profile: Profile
    reasoner: Reasoner
    workflow: Workflow


class Agent(ABC):
    """Agent implementation.

    Attributes:
        _id (str): The unique identifier of the agent.
        _profile (Profile): The profile of the agent.
        _workflow (Workflow): The workflow of the agent.
        _reasoner (Reasoner): The reasoner of the agent.
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        id: Optional[str] = None,
    ):
        self._id = id or str(uuid4())
        self._profile: Profile = agent_config.profile
        self._workflow: Workflow = agent_config.workflow
        self._reasoner: Reasoner = agent_config.reasoner

    def get_id(self) -> str:
        """Get the unique identifier of the agent."""
        return self._id

    def get_profile(self) -> Profile:
        """Get the profile of the agent."""
        return self._profile

    @abstractmethod
    async def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> Any:
        """Execute the agent."""
