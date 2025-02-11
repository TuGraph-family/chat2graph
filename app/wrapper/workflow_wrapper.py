from typing import Optional, Union

from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.workflow import Workflow
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


class WorkflowWrapper:
    """Facade of the workflow."""

    def __init__(self, workflow: Optional[Workflow] = None):
        self._workflow: Workflow = workflow or DbgptWorkflow()

    def chain(self, *operator_chain: Union[Operator, tuple[Operator, Operator]]) -> Workflow:
        """Chain the operators in the workflow."""
        for item in operator_chain:
            if isinstance(item, Operator):
                self._workflow.add_operator(item)
            elif (
                isinstance(item, tuple)
                and len(item) == 2
                and isinstance(item[0], Operator)
                and isinstance(item[1], Operator)
            ):
                self._workflow.add_operator(item[0], next_ops=[item[1]])
                self._workflow.add_operator(item[1], previous_ops=[item[0]])
            else:
                raise ValueError(f"Invalid chain item: {item}.")

        return self._workflow
