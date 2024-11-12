from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.agent.base_agent.base_agent import BaseAgent


class BaseReasoner(ABC):
    """Base Reasoner, an env element of the multi-agent system."""

    def __init__(self, agents: List[BaseAgent]):
        self.agent_dict: Dict[str, BaseAgent] = {
            agent.id: agent for agent in agents
        }  # agent_id: agent

    @abstractmethod
    async def infer(self, data: Any):
        """Infer from the data."""

    @abstractmethod
    async def update_knowledge(self, data: Any):
        """Update the knowledge."""

    @abstractmethod
    async def evaluate(self):
        """Evaluate the inference process."""

    @abstractmethod
    async def refine(self):
        """Refine the inference results."""
