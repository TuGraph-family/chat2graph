from typing import Optional

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
from app.manager.job_manager import JobManager
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
        # TODO: configure the chat2graph service by yaml

        # initialize the job manager
        self._job_manager = JobManager()

        # initialize the leader
        self._reasoner = DualModelReasoner()
        self._leader = Leader(agent_config=get_leader_config(reasoner=self._reasoner))

        # configure the multi-agent system
        self._leader.state.create_expert(graph_modeling_expert_config)
        self._leader.state.create_expert(data_importation_expert_config)
        self._leader.state.create_expert(graph_query_expert_config)
        self._leader.state.create_expert(graph_analysis_expert_config)

    async def execute(self, message: ChatMessage) -> ChatMessage:
        """Execute the service synchronously."""
        job = Job(goal=message.get_payload())
        await self._leader.execute_job(job=job)
        job_result: JobResult = await self._job_manager.query_job_result(job_id=job.id)
        return job_result.result

    def session(self, session_id: Optional[str] = None) -> Session:
        """Get the session, if not exists or session_id is None, create a new one."""
        return SessionManager().get_session(session_id=session_id)
