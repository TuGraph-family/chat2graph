from typing import List, Optional, Tuple, Union

from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.toolkit.action import Action
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig


class OperatorWrapper:
    """Facade of the operator."""

    def __init__(self):
        self._operator: Optional[Operator] = None

        self._instruction: Optional[str] = None
        self._output_schema: Optional[str] = None
        self._actions: List[Action] = []

    @property
    def operator(self) -> Operator:
        """Get the operator."""
        if not self._operator:
            raise ValueError("Operator is not built yet.")
        return self._operator

    def instruction(self, instruction: str) -> "OperatorWrapper":
        """Set the instruction of the operator."""
        self._instruction = instruction
        return self

    def output_schema(self, output_schema: str) -> "OperatorWrapper":
        """Set the output schema of the operator."""
        self._output_schema = output_schema
        return self

    def actions(self, actions: List[Action]) -> "OperatorWrapper":
        """Set the actions of the operator."""
        self._actions.extend(actions)
        return self

    def build(self) -> "OperatorWrapper":
        """Build the operator."""
        if not self._instruction:
            raise ValueError("Instruction is required.")
        if not self._output_schema:
            raise ValueError("Output schema is required.")

        config = OperatorConfig(
            instruction=self._instruction,
            output_schema=self._output_schema,
            actions=self._actions,
        )

        self._operator = Operator(config=config)

        return self

    def toolkit_chain(self, *action_chain: Union[Action, Tuple[Action, ...]]) -> "OperatorWrapper":
        """Chain the toolkit actions in the operator."""
        if not self._operator:
            raise ValueError("Operator is not built yet.")

        toolkit_wrapper = ToolkitWrapper(id=self.get_id())
        toolkit_wrapper.chain(*action_chain)

        return self

    def get_id(self) -> str:
        """Get the operator id."""
        if not self._operator:
            raise ValueError("Operator is not built yet.")
        return self._operator.get_id()
