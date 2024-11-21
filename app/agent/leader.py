from app.agent.agent import Agent, AgentConfig
from app.agent.leader_state import LeaderState


class Leader(Agent):
    """Leader is a role that can manage a group of agents and the tasks."""

    def __init__(self, agent_config: AgentConfig):
        super().__init__(agent_config)
        self._leader_state: LeaderState = LeaderState()

    async def execute(self):
        """Execute to resolve the task."""
