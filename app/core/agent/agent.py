from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional, cast

from app.core.model.artifact import Artifact, ContentType
from app.core.model.job import Job
from app.core.model.message import AgentMessage, GraphMessage, MessageType, WorkflowMessage
from app.core.reasoner.reasoner import Reasoner
from app.core.service.artifact_service import ArtifactService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.workflow.workflow import Workflow


@dataclass
class Profile:
    """Profile of the agent.

    Attributes:
        name (str): The name of the agent.
        description (str): The description of the agent.
    """

    name: str
    description: str = ""


@dataclass
class AgentConfig:
    """Configuration for the base agent.

    Attributes:
        profile (Profile): The profile of the agent.
        reasoner (Reasoner): The reasoner of the agent.
        workflow (Optional[Workflow]): The workflow of the agent.
    """

    # TODO: to be refactored (by yaml)
    profile: Profile
    reasoner: Reasoner
    workflow: Workflow


class Agent(ABC):
    """Agent implementation.

    Attributes:
        _id (str): The unique identifier of the agent.
        _profile (Profile): The profile of the agent.
        _workflow (Workflow): The workflow of the agent.
        _reasoner (Reasoner): The reasoner of the agent.
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        id: Optional[str] = None,
    ):
        # since the expert instance is not persisted, we mock the id with the agent name
        # TODO: persist the agent instance (leader and experts) in the database
        self._id: str = id or agent_config.profile.name + "_id"
        self._profile: Profile = agent_config.profile
        self._workflow: Workflow = agent_config.workflow
        self._reasoner: Reasoner = agent_config.reasoner

        self._message_service: MessageService = MessageService.instance
        self._job_service: JobService = JobService.instance
        self._artifact_service: ArtifactService = ArtifactService.instance

    def get_id(self) -> str:
        """Get the unique identifier of the agent."""
        return self._id

    def get_profile(self) -> Profile:
        """Get the profile of the agent."""
        return self._profile

    @abstractmethod
    def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> Any:
        """Execute the agent."""

    def save_output_agent_message(
        self, job: Job, workflow_message: WorkflowMessage, lesson: Optional[str] = None
    ) -> AgentMessage:
        """Save the agent message of the expert as an output message."""

        # collect the ids of the artifacts that handled in the workflow
        # TODO: how to define the selection of the artifacts to persist?
        artifact_ids: List[str] = []

        # get the graph artifacts by hard coding and then persist them into the graph messages
        graph_artifacts: List[Artifact] = self._artifact_service.get_artifacts_by_job_id_and_type(
            job_id=job.id,
            content_type=ContentType.GRAPH,
        )
        for graph_artifact in graph_artifacts:
            graph_message = GraphMessage(
                payload=cast(dict, graph_artifact.content),
                job_id=graph_artifact.source_reference.job_id,
                session_id=graph_artifact.source_reference.session_id,
            )
            graph_message_id = self._message_service.save_message(message=graph_message).get_id()
            artifact_ids.append(graph_message_id)

        # delete the all the temp artifacts for the (sub)job
        self._artifact_service.delete_artifacts_by_job_id(job_id=job.id)

        try:
            existed_expert_message: AgentMessage = cast(
                AgentMessage,
                self._message_service.get_message_by_job_id(
                    job_id=job.id, message_type=MessageType.AGENT_MESSAGE
                )[0],
            )
            expert_message: AgentMessage = AgentMessage(
                id=existed_expert_message.get_id(),
                job_id=job.id,
                payload=workflow_message.scratchpad,
                workflow_messages=[workflow_message],
                artifact_ids=artifact_ids,
                timestamp=existed_expert_message.get_timestamp(),
                lesson=lesson or existed_expert_message.get_lesson(),
            )
        except Exception:
            # if the agent message is not found, create a new agent message
            expert_message = AgentMessage(
                job_id=job.id,
                payload=workflow_message.scratchpad,
                workflow_messages=[workflow_message],
                artifact_ids=artifact_ids,
                lesson=lesson,
            )
        self._message_service.save_message(message=expert_message)

        return expert_message
