from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import uuid4

from app.agent.reasoner.base_reasoner import BaseReasoner
from app.agent.reasoner.dual_llm import DualLLMReasoner
from app.agent.workflow.workflow import Workflow
from app.memory.task import Task


@dataclass
class Profile(ABC):
    """The profile of the agent.

    Attributes:
        name (str): The name of the agent.
        description (str): The description of the agent.
    """

    name: str
    description: str = ""


@dataclass
class BaseAgentConfig:
    """Configuration for the base agent.

    Attributes:
        profile (Profile): The profile of the agent.
        workflow (Workflow): The workflow of the agent.
    """

    profile: Profile
    workflow: Workflow


class BaseAgent(ABC):
    """Base agent implementation.

    Attributes:
        id (str): The unique identifier of the agent.
        profile (Profile): The profile of the agent.
        workflow (Workflow): The workflow of the agent.
        reasoner (BaseReasoner): The reasoner of the agent.
        task (Task): The task assigned to the agent.
    """

    def __init__(
        self,
        task: Task,
        agent_config: BaseAgentConfig,
    ):
        self.id = str(uuid4())
        self.profile = agent_config.profile
        self.workflow = agent_config.workflow
        self.reasoner: BaseReasoner = DualLLMReasoner(task=task)
        self.task = task

    @abstractmethod
    async def execute(self):
        """Execute the agent."""

    async def decompose_task(self, task: Task, n_subtasks: int = 2):
        """Decompose the task into sub-tasks."""
