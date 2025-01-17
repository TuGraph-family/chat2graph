from typing import List, Optional, Tuple

from dbgpt.core.awel import MapOperator  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.memory.message import WorkflowMessage


class DbgptMapOperator(MapOperator[Tuple[Job, Optional[List[WorkflowMessage]]], WorkflowMessage]):
    """DB-GPT map operator"""

    def __init__(self, operator: Operator, reasoner: Reasoner, **kwargs):
        super().__init__(**kwargs)
        self._operator: Operator = operator
        self._reasoner: Reasoner = reasoner

    async def map(
        self, input_value: Tuple[Job, Optional[List[WorkflowMessage]], Optional[str]]
    ) -> WorkflowMessage:
        """Execute the operator."""
        job, workflow_messages, lesson = input_value
        return await self._operator.execute(
            reasoner=self._reasoner, job=job, workflow_messages=workflow_messages, lesson=lesson
        )
