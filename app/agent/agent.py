from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.workflow import Workflow
from app.memory.message import AgentMessage


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
        id (str): The unique identifier of the agent.
        profile (Profile): The profile of the agent.
        workflow (Workflow): The workflow of the agent.
        reasoner (Reasoner): The reasoner of the agent.
        job (Job): The job assigned to the agent.
    """

    def __init__(
        self,
        agent_config: AgentConfig,
    ):
        self._id = str(uuid4())
        self._profile: Profile = agent_config.profile
        self._workflow: Workflow = agent_config.workflow
        self._reasoner: Reasoner = agent_config.reasoner

    def get_id(self) -> str:
        """Get the unique identifier of the agent."""
        return self._id

    @abstractmethod
    async def execute(self, agent_message: AgentMessage) -> AgentMessage:
        """Execute the agent."""
