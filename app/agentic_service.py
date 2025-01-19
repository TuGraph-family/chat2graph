import asyncio

from app.agent.agent import AgentConfig, Profile
from app.agent.leader import Leader
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.memory.message import UserMessage
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from example.run_graph_modeling import get_graph_modeling_workflow

graph_modeling_workflow = get_graph_modeling_workflow()


class AgenticService:
    """Agenttic service class"""

    def __init__(self):
        # TODO: to be configured (by yaml)
        reasoner = DualModelReasoner()
        agent_config = AgentConfig(
            profile=Profile(name="leader"), reasoner=reasoner, workflow=DbgptWorkflow()
        )
        self._leader: Leader = Leader(agent_config=agent_config)

    async def execute(self, user_message: UserMessage) -> None:
        """Execute the service"""

        asyncio.create_task(self._leader.receive_message(user_message=user_message))

    async def query_result(self, session_id: str) -> UserMessage:
        """Query the result"""
        return await self._leader.query_state(session_id=session_id)
