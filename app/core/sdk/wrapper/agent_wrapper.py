from typing import Optional, Tuple, Union

from app.core.agent.agent import Agent, AgentConfig, Profile
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.type import PlatformType
from app.core.model.message import MessageSourceType
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.reasoner_wrapper import ReasonerWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.service.agent_service import AgentService
from app.core.workflow.workflow import Workflow


class AgentWrapper:
    """Facade of the agent."""

    def __init__(self):
        self._agent: Optional[Agent] = None

        self._type: Optional[Union[type[Leader], type[Expert]]] = None
        self._profile: Optional[Profile] = None
        self._reasoner: Optional[Reasoner] = None
        self._workflow: Optional[Workflow] = None

    @property
    def agent(self) -> Agent:
        """Get the agent."""
        if not self._agent:
            raise ValueError("Agent is not set.")
        return self._agent

    def type(self, agent_type: Union[type[Leader], type[Expert]]) -> "AgentWrapper":
        """Set the type of the agent (Leader or Expert)."""
        if agent_type not in [Leader, Expert]:
            raise ValueError("Invalid agent type. Must be Leader or Expert.")
        self._type = agent_type
        return self

    def profile(self, name: str, description: Optional[str] = None) -> "AgentWrapper":
        """Set the profile of the agent."""
        self._profile = Profile(name=name, description=description or "")
        return self

    def reasoner(
        self, actor_name: str = MessageSourceType.MODEL.value, thinker_name: Optional[str] = None
    ) -> "AgentWrapper":
        """Set the reasoner of the expert."""
        self._reasoner = (
            ReasonerWrapper().build(actor_name=actor_name, thinker_name=thinker_name).reasoner
        )

        return self

    def workflow(
        self,
        *operator_chain: Union[OperatorWrapper, Tuple[OperatorWrapper, ...]],
        platfor_type: Optional[PlatformType] = None,
    ) -> "AgentWrapper":
        """Set the workflow of the expert."""

        if self._workflow:
            workflow_wrapper = WorkflowWrapper(workflow=self._workflow)
            self._workflow = workflow_wrapper.chain(*operator_chain).workflow
        else:
            self._workflow = WorkflowWrapper(platform=platfor_type).chain(*operator_chain).workflow
        return self

    def clear(self) -> "AgentWrapper":
        """Clear the agent wrapper."""
        self._type = None
        self._profile = None
        self._reasoner = None
        self._workflow = None
        return self

    def build(self) -> "AgentWrapper":
        """Build the agent."""
        if not self._profile:
            raise ValueError("Profile is required.")
        if not self._workflow:
            raise ValueError("Workflow is required.")
        if not self._type:
            raise ValueError("Agent type is required. Please use .type(Leader) or .type(Expert).")

        agent_config = AgentConfig(
            profile=self._profile,
            reasoner=self._reasoner or DualModelReasoner(),
            workflow=self._workflow,
        )

        agent_service: AgentService = AgentService.instance

        if self._type is Leader:
            self.clear()
            self._agent = Leader(agent_config=agent_config)
            agent_service.set_leadder(self._agent)
        if self._type is Expert:
            self.clear()
            self._agent = Expert(agent_config=agent_config)
            agent_service.add_expert(self._agent)

        return self
