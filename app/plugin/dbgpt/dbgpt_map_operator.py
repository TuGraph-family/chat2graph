from typing import List, Optional, Tuple, Union

from dbgpt.core.awel import MapOperator  # type: ignore

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.memory.message import WorkflowMessage


class DbgptMapOperator(
    MapOperator[Tuple[Job, Optional[List[WorkflowMessage]]], WorkflowMessage]
):
    """DB-GPT map operator"""

    def __init__(self, operator: Operator, reasoner: Reasoner, **kwargs):
        super().__init__(**kwargs)
        self._operator: Operator = operator
        self._reasoner: Reasoner = reasoner

    async def map(
        self, input_value: Union[Tuple[Job, Optional[List[WorkflowMessage]]], Job]
    ) -> WorkflowMessage:
        """Execute the operator."""

        # if the operator is an initial operator in DAG
        if isinstance(input_value, Job):
            job = input_value
            return await self._operator.execute(reasoner=self._reasoner, job=job)

        # else, the operator receives the output of the previous operator
        # since the workflow_messages are not None
        job, workflow_messages = input_value
        return await self._operator.execute(
            reasoner=self._reasoner, job=job, workflow_messages=workflow_messages
        )
