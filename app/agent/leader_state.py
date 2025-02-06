import threading
from typing import Dict, List

from app.agent.agent import AgentConfig, Profile
from app.agent.expert import Expert
from app.common.singleton import Singleton


class LeaderState(metaclass=Singleton):
    """Leader State is uesd to manage expert agent and jobs.

    attributes:
        _expert_instances (Dict[str, Expert]): it stores the expert agent instances.
        _expert_creation_lock (threading.Lock): it is used to lock the expert creation.
    """

    def __init__(self):
        self._expert_instances: Dict[str, Expert] = {}  # expert_id -> instance
        self._expert_creation_lock: threading.Lock = threading.Lock()

    def get_expert_by_name(self, expert_name: str) -> Expert:
        """Get existing expert instance or create a new one."""
        # get expert ID by expert name
        for expert in self._expert_instances.values():
            if expert.get_profile().name == expert_name:
                return expert
        raise ValueError(f"Expert {expert_name} not exists in the leader state.")

    def get_expert_by_id(self, expert_id: str) -> Expert:
        """Get existing expert instance or create a new one."""
        return self._expert_instances[expert_id]

    def get_expert_profiles(self) -> Dict[str, Profile]:
        """Return a dictionary of all registered expert profiles."""
        expert_profiles: Dict[str, Profile] = {}
        for _, expert in self._expert_instances.items():
            expert_profiles[expert.get_id()] = expert.get_profile()

        return expert_profiles

    def list_experts(self) -> List[Expert]:
        """Return a list of all registered expert information."""
        return list(self._expert_instances.values())

    def create_expert(self, agent_config: AgentConfig) -> Expert:
        """Add an expert profile to the registry."""
        with self._expert_creation_lock:
            expert = Expert(agent_config=agent_config)
            expert_id = expert.get_id()
            self._expert_instances[expert_id] = expert
            return expert

    def release_expert(self, expert_id: str) -> None:
        """Release the expert"""
        self._expert_instances.pop(expert_id, None)
