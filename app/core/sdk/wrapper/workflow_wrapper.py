from typing import Any, Optional, Tuple, Union

from app.core.workflow.operator import Operator
from app.core.workflow.workflow import Workflow
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


class WorkflowWrapper:
    """Facade of the workflow."""

    def __init__(self, workflow: Optional[Workflow] = None):
        self._workflow: Workflow = workflow or DbgptWorkflow()

    def chain(self, *operator_chain: Union[Operator, Tuple[Operator, ...]]) -> Workflow:
        """Chain the operators in the workflow.

        If a tuple of operators is provided, they will be chained sequentially.
        """
        for item in operator_chain:
            if isinstance(item, Operator):
                self._workflow.add_operator(item)
            elif isinstance(item, tuple) and all(isinstance(op, Operator) for op in item):
                # chain all operators in the tuple sequentially
                for i in range(len(item) - 1):
                    self._workflow.add_operator(item[i], next_ops=[item[i + 1]])
                    self._workflow.add_operator(item[i + 1], previous_ops=[item[i]])
            else:
                raise ValueError(f"Invalid chain item: {item}.")

        return self._workflow

    def add_operator(
        self,
        operator: Operator,
        previous_op: Optional[Operator] = None,
        next_op: Optional[Operator] = None,
    ) -> Workflow:
        """Add an operator to the workflow.

        Orignal structure:
            previous operator -> Next operator
        After adding:
            previous operator -> Operator -> Next operator
        """
        # TODO: Implement the add_operator method
        raise NotImplementedError("This method is not implemented")

    def update_operator(self, operator: Operator) -> Workflow:
        """Update the operator in the workflow."""
        self._workflow.update_operator(operator)
        return self._workflow

    def remove_operator(self, operator: Operator) -> Workflow:
        """Remove the operator from the workflow.

        Orignal structure:
            previous operator 1 -> Operator -> Next operator 1
            previous operator 2 -> Operator -> Next operator 2
        After removing:
            previous operator 1 -> Next operator 1
            previous operator 1 -> Next operator 2
            previous operator 2 -> Next operator 1
            previous operator 2 -> Next operator 2
        """
        # TODO: Implement the remove_operator method
        raise NotImplementedError("This method is not implemented.")

    def train(self, *args: Any, **kwargs: Any) -> Any:
        """Train and auto-generate the workflow."""
        # TODO: Implement the train method
        raise NotImplementedError("This method is not implemented")
