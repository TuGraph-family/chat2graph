import asyncio

from app.agent.agent import AgentConfig, Profile
from app.agent.graph_agent.data_importation import get_data_importation_expert_config
from app.agent.graph_agent.graph_analysis import get_graph_analysis_expert_config
from app.agent.graph_agent.graph_modeling import get_graph_modeling_expert_config
from app.agent.graph_agent.graph_query import get_graph_query_expert_config
from app.agent.graph_agent.question_answering import get_graph_question_answeing_expert_config
from app.agent.leader import Leader
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA, JOB_DECOMPOSITION_PROMPT
from app.memory.message import UserMessage
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow

graph_modeling_expert_config = get_graph_modeling_expert_config()
data_importation_expert_config = get_data_importation_expert_config()
graph_query_expert_config = get_graph_query_expert_config()
graph_analysis_expert_config = get_graph_analysis_expert_config()
graph_question_answering_expert_config = get_graph_question_answeing_expert_config()


class AgenticService:
    """Agenttic service class"""

    def __init__(self):
        # TODO: to be configured (by yaml)
        reasoner = DualModelReasoner()

        # configure the leader
        decomp_operator_config = OperatorConfig(
            id="job_decomp_operator_id",
            instruction=JOB_DECOMPOSITION_PROMPT,
            actions=[],
            output_schema=JOB_DECOMPOSITION_OUTPUT_SCHEMA,
        )
        decomposition_operator = Operator(config=decomp_operator_config)
        leader_workflow = DbgptWorkflow()
        leader_workflow.add_operator(decomposition_operator)
        agent_config = AgentConfig(
            profile=Profile(name="leader"), reasoner=reasoner, workflow=leader_workflow
        )
        self._leader: Leader = Leader(agent_config=agent_config)

        self._leader.get_leader_state().add_expert_config(graph_modeling_expert_config)
        self._leader.get_leader_state().add_expert_config(data_importation_expert_config)
        self._leader.get_leader_state().add_expert_config(graph_query_expert_config)
        self._leader.get_leader_state().add_expert_config(graph_analysis_expert_config)

    async def execute(self, user_message: UserMessage) -> None:
        """Execute the service"""

        asyncio.create_task(self._leader.receive_message(user_message=user_message))

    async def query_result(self, session_id: str) -> UserMessage:
        """Query the result"""
        return await self._leader.query_state(session_id=session_id)
