from typing import List

from app.core.agent.agent import AgentConfig
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.singleton import Singleton


class AgentService(metaclass=Singleton):
    """Leader service"""

    def __init__(self):
        # initialize the leader
        self._leaders: List[Leader] = []

    def set_leadder(self, leader: Leader) -> None:
        """Set the leader. The agent service now manages only one leader."""
        self._leaders = [leader]

    def create_expert(self, expert_config: AgentConfig) -> None:
        """Create an expert and add it to the leader."""
        self.leader.state.create_expert(expert_config)

    def add_expert(self, expert: Expert) -> None:
        """Add an expert to the leader."""
        self.leader.state.add_expert(expert)

    @property
    def leader(self) -> Leader:
        """Get the leader. The agent service now manages only one leader."""
        if len(self._leaders) == 0:
            raise ValueError("No leader found.")
        return self._leaders[0]
