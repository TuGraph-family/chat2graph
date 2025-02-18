from typing import Any, Optional

from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.singleton import Singleton
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.sdk.legacy.data_importation import get_data_importation_expert_config
from app.core.sdk.legacy.graph_analysis import get_graph_analysis_expert_config
from app.core.sdk.legacy.graph_modeling import get_graph_modeling_expert_config
from app.core.sdk.legacy.graph_query import get_graph_query_expert_config
from app.core.sdk.legacy.leader_config import get_leader_config
from app.core.sdk.legacy.question_answering import get_graph_question_answeing_expert_config
from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.service.agent_service import AgentService
from app.core.service.job_service import JobService
from app.core.service.session_service import SessionService
from app.core.service.toolkit_service import ToolkitService

graph_modeling_expert_config = get_graph_modeling_expert_config()
data_importation_expert_config = get_data_importation_expert_config()
graph_query_expert_config = get_graph_query_expert_config()
graph_analysis_expert_config = get_graph_analysis_expert_config()
graph_question_answering_expert_config = get_graph_question_answeing_expert_config()


class AgenticService(metaclass=Singleton):
    """Agentic service class"""

    def __init__(self, service_name: Optional[str] = None):
        self._service_name = service_name or "Chat2Graph"

        # initialize the services
        self._session_service = SessionService()
        self._agent_service = AgentService()
        self._job_service = JobService()
        self._toolkit_service = ToolkitService()

    def session(self, session_id: Optional[str] = None) -> SessionWrapper:
        """Get the session, if not exists or session_id is None, create a new one."""
        return SessionWrapper().session(session_id=session_id)

    async def execute(self, message: ChatMessage) -> ChatMessage:
        """Execute the service synchronously."""
        job_wrapper = JobWrapper(Job(goal=message.get_payload()))

        # execute the job
        await job_wrapper.execute()

        # get the result of the job
        job_result: JobResult = await job_wrapper.result()
        return job_result.result

    def load(self, config_file_path: Optional[str] = None) -> "AgenticService":
        """Load the configuration of the agentic service."""
        if not config_file_path:
            self.load_default()
            return self

        # TODO: configure the chat2graph service by yaml

        return self

    def load_default(self) -> None:
        """Load the default configuration of the agentic service."""
        # TODO: load the default yaml configuration

        # initialize the leader
        self._agent_service.set_leadder(
            Leader(agent_config=get_leader_config(reasoner=DualModelReasoner()))
        )

        # configure the multi-agent system
        self._agent_service.create_expert(graph_modeling_expert_config)
        self._agent_service.create_expert(data_importation_expert_config)
        self._agent_service.create_expert(graph_query_expert_config)
        self._agent_service.create_expert(graph_analysis_expert_config)

    def train_toolkit(self, id: str, *args, **kwargs) -> Any:
        """Train the toolkit."""
        self._toolkit_service.train(id=id, *args, **kwargs)

    def train_workflow(self, workflow_wrapper: WorkflowWrapper, *args, **kwargs) -> Any:
        """Train the workflow."""
        # TODO: implement the train workflow
        raise NotImplementedError("Train workflow is not implemented yet.")

    def leader(self, name: str, description: Optional[str] = None) -> AgentWrapper:
        """Set the name of the leader."""
        agent_wrapper = AgentWrapper()
        agent_wrapper.name(name).description(description).type(Leader)

        return agent_wrapper

    def expert(self, name: str, description: Optional[str] = None) -> AgentWrapper:
        """Set the name of the expert."""
        agent_wrapper = AgentWrapper()
        agent_wrapper.name(name).description(description).type(Expert)

        return agent_wrapper
