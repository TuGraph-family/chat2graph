from typing import List, Optional, Tuple

from dbgpt.core.awel import MapOperator  # type: ignore

from app.core.model.job import Job
from app.core.model.message import WorkflowMessage
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator


class DbgptMapOperator(MapOperator[Tuple[Job, Optional[List[WorkflowMessage]]], WorkflowMessage]):
    """DB-GPT map operator"""

    def __init__(self, operator: Operator, reasoner: Reasoner, **kwargs):
        super().__init__(**kwargs)
        self._operator: Operator = operator
        self._reasoner: Reasoner = reasoner

    def map(
        self, input_value: Tuple[Job, Optional[List[WorkflowMessage]], Optional[str]]
    ) -> WorkflowMessage:
        """Execute the operator."""
        job, workflow_messages, lesson = input_value
        return self._operator.execute(
            reasoner=self._reasoner, job=job, workflow_messages=workflow_messages, lesson=lesson
        )
