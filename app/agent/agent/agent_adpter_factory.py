from enum import Enum
from typing import Optional

from app.agent.agent.agent_adapter import AgentAdapter
from app.agent.agent.dbgpt_agent_adapter import DBGPTAgentAdapter


class AgentFrameworkName(Enum):
    """Agent Framework Name."""

    DBGPT = "dbgpt"
    # METAGPT = "metagpt"  # TODO: Add MetaGPT agent adapter


class AgentAdapterFactory:
    """Agent Adapter Factory."""

    @classmethod
    async def create(
        cls, agent_type: AgentFrameworkName, **kwargs
    ) -> Optional[AgentAdapter]:
        """Create an agent."""
        if agent_type == AgentFrameworkName.DBGPT:
            dbgpt_agent_adapter = DBGPTAgentAdapter(**kwargs)
            await dbgpt_agent_adapter.init_client()
            return dbgpt_agent_adapter
        raise ValueError(f"Cannot create agent of type {agent_type}")

    @classmethod
    async def regist(cls, agent_type: str, adapter: AgentAdapter) -> None:
        """Register an agent."""
        # TODO: Implement agent registration
