import asyncio

from openai.resources.fine_tuning import JobsWithRawResponse

from app.agent.core.session import Session
from app.agent.graph_agent.data_importation import get_data_importation_expert_config
from app.agent.graph_agent.graph_analysis import get_graph_analysis_expert_config
from app.agent.graph_agent.graph_modeling import get_graph_modeling_expert_config
from app.agent.graph_agent.graph_query import get_graph_query_expert_config
from app.agent.graph_agent.leader_config import get_leader_config
from app.agent.graph_agent.question_answering import get_graph_question_answeing_expert_config
from app.agent.job import Job
from app.agent.job_result import JobResult
from app.agent.leader import Leader
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.manager.session_manager import SessionManager
from app.memory.message import ChatMessage

graph_modeling_expert_config = get_graph_modeling_expert_config()
data_importation_expert_config = get_data_importation_expert_config()
graph_query_expert_config = get_graph_query_expert_config()
graph_analysis_expert_config = get_graph_analysis_expert_config()
graph_question_answering_expert_config = get_graph_question_answeing_expert_config()

class AgenticService:
    """Agentic service class"""

    def __init__(self):
        # TODO: to be configured by yaml
        reasoner = DualModelReasoner()
        self._leader: Leader = Leader(agent_config=get_leader_config(reasoner=reasoner))

        self._leader.get_leader_state().add_expert_config(graph_modeling_expert_config)
        self._leader.get_leader_state().add_expert_config(data_importation_expert_config)
        self._leader.get_leader_state().add_expert_config(graph_query_expert_config)
        self._leader.get_leader_state().add_expert_config(graph_analysis_expert_config)

    def execute(self, user_message: ChatMessage) -> ChatMessage:
        pass

    def get_session_manager(self) -> SessionManager:
        pass

