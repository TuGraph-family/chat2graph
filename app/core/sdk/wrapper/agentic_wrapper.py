from typing import Union

from app.core.sdk.wrapper.agent_wrapper import AgentWrapper
from app.core.sdk.wrapper.operator_wrapper import OperatorWrapper
from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.sdk.wrapper.workflow_wrapper import WorkflowWrapper
from app.core.toolkit.action import Action


class AgenticWrapper:
    """Facade of the agentic system."""

    def __init__(self):
        self._agent_wrapper: AgentWrapper = AgentWrapper()
        self._operator_wrapper: OperatorWrapper = OperatorWrapper()
        self._workflow_wrapper: WorkflowWrapper = WorkflowWrapper()
        self._toolkit_wrapper: ToolkitWrapper = ToolkitWrapper()

    def toolkit_chain(
        self, *action_chain: Union[Action, tuple[Action, Action]]
    ) -> "AgenticWrapper":
        """Chain actions together in the toolkit graph."""
        self._toolkit_wrapper.chain(*action_chain)
        return self
