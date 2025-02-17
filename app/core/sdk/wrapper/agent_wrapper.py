from typing import Optional, Union

from app.core.agent.agent import Agent, AgentConfig, Profile
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.sdk.wrapper.reasoner_wrapper import ReasonerWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.workflow.workflow import Workflow


class AgentWrapper:
    """Facade of the agent."""

    def __init__(self):
        self._agent: Optional[Agent] = None

        self._type: Optional[Union[type[Leader], type[Expert]]] = None
        self._name: Optional[str] = None
        self._description: str = ""
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

    def name(self, name: str) -> "AgentWrapper":
        """Set the name of the agent."""
        self._name = name
        return self

    def description(self, description: str) -> "AgentWrapper":
        """Set the description of the agent."""
        self._description = description
        return self

    def reasoner(self, reasoner_wrapper: ReasonerWrapper) -> "AgentWrapper":
        """Set the reasoner of the agent."""
        self._reasoner = reasoner_wrapper.reasoner
        return self

    def workflow(self, workflow_wrapper: WorkflowWrapper) -> "AgentWrapper":
        """Set the workflow of the agent."""
        self._workflow = workflow_wrapper.workflow
        return self

    def clear(self) -> "AgentWrapper":
        """Clear the agent wrapper."""
        self._type = None
        self._name = None
        self._description = ""
        self._reasoner = None
        self._workflow = None
        return self

    def build(self) -> "AgentWrapper":
        """Build the agent."""
        if not self._name:
            raise ValueError("Name is required.")
        if not self._workflow:
            raise ValueError("Workflow is required.")
        if not self._type:
            raise ValueError("Agent type is required. Please use .type(Leader) or .type(Expert).")

        agent_config = AgentConfig(
            profile=Profile(name=self._name, description=self._description),
            reasoner=self._reasoner or DualModelReasoner(),
            workflow=self._workflow,
        )

        if self._type is Leader:
            self.clear()
            self._agent = Leader(agent_config=agent_config)
        if self._type is Expert:
            self.clear()
            self._agent = Expert(agent_config=agent_config)

        return self
