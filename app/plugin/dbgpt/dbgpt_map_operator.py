from typing import List, Optional, Tuple

from dbgpt.core.awel import MapOperator  # type: ignore

from app.core.model.job import Job
from app.core.model.message import WorkflowMessage
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator


class DbgptMapOperator(
    MapOperator[
        Tuple[Job, List[WorkflowMessage], List[WorkflowMessage], Optional[str]], WorkflowMessage
    ]
):
    """DB-GPT map operator"""

    def __init__(self, operator: Operator, reasoner: Reasoner, **kwargs):
        super().__init__(**kwargs)
        self._operator: Operator = operator
        self._reasoner: Reasoner = reasoner

    async def map(
        self, input_value: Tuple[Job, List[WorkflowMessage], List[WorkflowMessage], Optional[str]]
    ) -> WorkflowMessage:
        """Execute the operator.

        Args:
            input_value (Tuple[Job, List[WorkflowMessage], List[WorkflowMessage], Optional[str]]):
                The input value, which is a tuple of the job assigned to the expert,
                the outputs of previous experts, the outputs of previous operators,
                and the lesson learned (provided by the successor expert).

        Returns:
            WorkflowMessage: The output message of the operator.
        """
        job, previous_expert_outputs, previous_operator_outputs, lesson = input_value
        return await self._operator.execute(
            reasoner=self._reasoner,
            job=job,
            workflow_messages=previous_operator_outputs,
            previous_expert_outputs=previous_expert_outputs,
            lesson=lesson,
        )
