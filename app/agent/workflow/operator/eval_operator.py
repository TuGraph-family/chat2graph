from typing import List, Optional

from app.agent.job import Job
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator import Operator
from app.commom.util import parse_json
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
        (
            rec_tools,
            rec_actions,
        ) = await self._toolkit_service.get_toolkit().recommend_tools(
            actions=self._config.actions,
            threshold=self._config.threshold,
            hops=self._config.hops,
        )

        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=workflow_messages,
            tools=rec_tools,
            actions=rec_actions,
            knowledge=await self.get_knowledge(),
            insights=await self.get_env_insights(),
        )

        result = await reasoner.infer(task=task)

        result_dict = parse_json(text=result)

        return WorkflowMessage(
            content={
                "scratchpad": result_dict["deliverable"],
                "status": result_dict["status"],
                "experience": result_dict["experience"],
            }
        )
