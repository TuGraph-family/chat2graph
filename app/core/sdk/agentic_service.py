from typing import Any, Optional

from app.core.agent.expert import Expert
from app.core.common.singleton import Singleton
from app.core.model.job import Job
from app.core.model.job_result import JobResult
from app.core.model.message import ChatMessage
from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.job_wrapper import JobWrapper
from app.core.sdk.wrapper.session_wrapper import SessionWrapper
from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper


class AgenticService(metaclass=Singleton):
    """Agentic service class"""

    def __init__(self, service_name: Optional[str] = None):
        self._service_name = service_name or "Chat2Graph"

        # initialize wrappers
        self._session_wrapper = SessionWrapper()
        self._agent_wrapper = AgentWrapper()
        self._job_wrapper = JobWrapper()

    def session(self, session_id: Optional[str] = None) -> SessionWrapper:
        """Get the session, if not exists or session_id is None, create a new one."""
        return self._session_wrapper.session(session_id=session_id)

    async def execute(self, message: ChatMessage) -> ChatMessage:
        """Execute the service synchronously."""
        job = Job(goal=message.get_payload())
        await self._job_wrapper.execute_job(job=job)

        job_result: JobResult = await self._job_wrapper.query_job_result(id=job.id)
        return job_result.result

    def expert(self, expert: Expert) -> None:
        """Add the expert to the agentic service."""
        self._agent_wrapper.expert(expert)

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

    def train_toolkit(self, toolkit_wrapper: ToolkitWrapper, *args, **kwargs) -> Any:
        """Train the toolkit."""
        toolkit_wrapper.train(*args, **kwargs)

    def train_workflow(self, workflow_wrapper: WorkflowWrapper, *args, **kwargs) -> Any:
        """Train the workflow."""
        workflow_wrapper.train(*args, **kwargs)
