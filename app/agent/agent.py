from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from app.agent.reasoner.dual_llm import DualModelReasoner
from app.agent.workflow.workflow import Workflow


@dataclass
class Profile:
    """The profile of the agent.

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
        workflow (Workflow): The workflow of the agent.
    """

    # TODO: to be refactored (yaml)
    profile: Profile
    workflow: Workflow


class Agent(ABC):
    """Agent implementation.

    Attributes:
        id (str): The unique identifier of the agent.
        profile (Profile): The profile of the agent.
        workflow (Workflow): The workflow of the agent.
        reasoner (DualModelReasoner): The reasoner of the agent.
        task (Task): The task assigned to the agent.
    """

    def __init__(
        self,
        agent_config: AgentConfig,
    ):
        self._id = str(uuid4())
        self._profile = agent_config.profile
        self._workflow = agent_config.workflow
        self._reasoner: DualModelReasoner = DualModelReasoner()

    @abstractmethod
    async def execute(self):
        """Execute the agent."""
