from abc import ABC
from typing import Any, Dict

from app.agent.base_agent import BaseAgentConfig
from app.agent.expert import ExpertAgent


class ExpertRegistry(ABC):
    """Registry for managing expert agent initialization information."""

    def __init__(self):
        # Store class and config information, not instances
        self._expert_dict: Dict[str, ExpertAgent] = {}  # expert_id -> expert_instance

    def register(self, expert_id: str, expert: ExpertAgent) -> None:
        """
        Register information needed to initialize an expert agent.
        """

        if expert_id in self._expert_dict:
            raise ValueError(f"Expert with ID {expert_id} already registered")

        # Store initialization information
        self._expert_dict[expert_id] = expert

    def create(
        self, expert_id: str, task, agent_config: BaseAgentConfig
    ) -> ExpertAgent:
        """
        Create a new instance of an expert agent.
        """
        if expert_id in self._expert_dict:
            raise ValueError(f"Expert with ID {expert_id} has been registered")
        expert = ExpertAgent(task=task, agent_config=agent_config)
        self._expert_dict[expert_id] = expert
        return expert

    def list_experts(self) -> Dict[str, Dict[str, Any]]:
        """Return a dictionary of all registered expert information."""

        return dict(self._expert_dict)
