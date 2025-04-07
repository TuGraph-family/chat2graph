from typing import Optional, Tuple, Union

from app.core.agent.agent import Agent, AgentConfig, Profile
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.common.type import WorkflowPlatformType
from app.core.prompt.eval_operator import (
    EVAL_OPERATION_INSTRUCTION_PROMPT,
    EVAL_OPERATION_OUTPUT_PROMPT,
)
from app.core.reasoner.reasoner import Reasoner
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.service.agent_service import AgentService
from app.core.service.reasoner_service import ReasonerService
from app.core.workflow.eval_operator import EvalOperator
from app.core.workflow.operator_config import OperatorConfig
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

    def reasoner(self, reasoner: Reasoner) -> "AgentWrapper":
        """Set the reasoner of the agent."""
        self._reasoner = reasoner
        return self

    def workflow(
        self,
        *operator_chain: Union[OperatorWrapper, Tuple[OperatorWrapper, ...]],
        platform_type: Optional[WorkflowPlatformType] = None,
    ) -> "AgentWrapper":
        """Set the workflow of the expert."""

        if self._workflow:
            workflow_wrapper = WorkflowWrapper(workflow=self._workflow)
            self._workflow = workflow_wrapper.chain(*operator_chain).workflow
        else:
            self._workflow = WorkflowWrapper(platform=platform_type).chain(*operator_chain).workflow
        return self

    def evaluator(self) -> "AgentWrapper":
        """Set the evaluator of the workflow."""
        evaluator = EvalOperator(
            config=OperatorConfig(
                instruction=EVAL_OPERATION_INSTRUCTION_PROMPT,
                actions=[],
                output_schema=EVAL_OPERATION_OUTPUT_PROMPT,
            )
        )
        if not self._workflow:
            raise ValueError(
                "Evaluator must be set after setting the workflow. Please use .workflow(*) first."
            )
        self._workflow.set_evaluator(evaluator)
        return self

    def build(self) -> "AgentWrapper":
        """Build the agent."""
        if not self._profile:
            raise ValueError("Profile is required.")
        if not self._reasoner:
            reasoner_service: ReasonerService = ReasonerService.instance
            self._reasoner = reasoner_service.get_reasoner()
        if not self._workflow:
            raise ValueError("Workflow is required.")
        if not self._type:
            raise ValueError("Agent type is required. Please use .type(Leader) or .type(Expert).")

        agent_config = AgentConfig(
            profile=self._profile,
            reasoner=self._reasoner,
            workflow=self._workflow,
        )

        agent_service: AgentService = AgentService.instance

        if self._type is Leader:
            self._agent = Leader(agent_config=agent_config)
            agent_service.set_leadder(self._agent)
        if self._type is Expert:
            self._agent = Expert(agent_config=agent_config)
            agent_service.add_expert(self._agent)

        return self
