from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from app.agent.profile import Profile
from app.agent.workflow.workflow import Workflow
from app.memory.task import Task


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
        self.agent_config = agent_config
        self.reasoner = None
        self.task = task

    @abstractmethod
    async def execute(self):
        """Execute the agent."""
