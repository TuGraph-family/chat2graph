from typing import List, Optional

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator import Operator
from app.common.util import parse_json
from app.memory.message import WorkflowMessage


class EvalOperator(Operator):
    """Operator for evaluating the performance of the model."""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
    ) -> WorkflowMessage:
        """Execute the operator by LLM client."""
        task = await self._build_task(job, workflow_messages)

        result = await reasoner.infer(task=task)

        result_dict = parse_json(text=result)

        return WorkflowMessage(
            content={
                "scratchpad": result_dict["deliverable"],
                "status": result_dict["status"],
                "experience": result_dict["experience"],
            }
        )
