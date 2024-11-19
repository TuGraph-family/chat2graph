from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from app.agent.reasoner.dual_llm import DualLLMReasoner
from app.agent.workflow.workflow import Workflow
from app.memory.task import Task


@dataclass
class Profile(ABC):
    """The profile of the agent."""

    name: str
    description: str = ""


@dataclass
class BaseAgentConfig:
    """Configuration for the base agent."""

    profile: Profile
    workflow: Workflow


class BaseAgent(ABC):
    """Base agent implementation."""

    def __init__(
        self,
        task: Task,
        agent_config: BaseAgentConfig,
    ):
        self.id = str(uuid4())
        self.profile = agent_config.profile
        self.workflow = agent_config.workflow
        self.reasoner: DualLLMReasoner = DualLLMReasoner(task=task)
        self.task = task

    @abstractmethod
    async def execute(self):
        """Execute the agent."""
