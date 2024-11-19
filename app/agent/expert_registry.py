from abc import ABC
from typing import Dict

from app.agent.base_agent import BaseAgentConfig
from app.agent.expert import ExpertAgent


class ExpertRegistry(ABC):
    """Registry for managing expert agent initialization information."""

    def __init__(self):
        # Store class and config information, not instances
        self._expert_dict: Dict[str, BaseAgentConfig] = {}  # expert_id -> expert_config

    def register(self, name: str, expert: BaseAgentConfig) -> None:
        """
        Register information needed to initialize an expert agent.
        """

        if name in self._expert_dict:
            raise ValueError(f"Expert {name} already registered")

        # Store initialization information
        self._expert_dict[name] = expert

    def create(self, name: str, task, agent_config: BaseAgentConfig) -> ExpertAgent:
        """
        Create a new instance of an expert agent.
        """
        if name in self._expert_dict:
            raise ValueError(f"Expert with ID {name} has been registered")
        expert = ExpertAgent(task=task, agent_config=agent_config)
        return expert

    def list_expert_configs(self) -> Dict[str, BaseAgentConfig]:
        """Return a dictionary of all registered expert information."""

        return dict(self._expert_dict)
