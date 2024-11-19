from app.agent.base_agent import BaseAgent, BaseAgentConfig
from app.agent.expert_registry import ExpertRegistry


class Leader(BaseAgent):
    """A leader is a role that can manage a group of agents and the tasks."""

    def __init__(
        self, task, agent_config: BaseAgentConfig, expert_registry: ExpertRegistry
    ):
        super().__init__(task, agent_config)
        self.agent_registry = expert_registry

    async def execute(self):
        """Execute to resolve the task."""
