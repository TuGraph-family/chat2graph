from typing import Any

from app.agent.base_agent import BaseAgent
from app.agent.reasoner.base_reasoner import BaseReasoner


class CoLLMReasoner(BaseReasoner):
    """CoLLM Reasoner."""

    def __init__(self, actor_agent: BaseAgent, thinker_agent: BaseAgent):
        super().__init__([actor_agent, thinker_agent])
        self.actor_agent = actor_agent
        self.thinker_agent = thinker_agent

    async def infer(self, data: Any):
        """Infer from the data."""

    async def update_knowledge(self, data: Any):
        """Update the knowledge."""

    async def evaluate(self):
        """Evaluate the inference process."""

    async def refine(self):
        """Refine the inference results."""
