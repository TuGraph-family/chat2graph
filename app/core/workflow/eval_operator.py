import json
from typing import List, Optional

from app.core.model.job import Job
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator
from app.core.common.type import WorkflowStatus
from app.core.common.util import parse_json
from app.core.model.message import WorkflowMessage


class EvalOperator(Operator):
    """Operator for evaluating the performance of the model."""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the operator by LLM client."""
        assert workflow_messages is not None and len(workflow_messages) > 0, (
            "There is no workflow message(s) to be evaluated."
        )

        job.context = "TARGET GOAL:\n" + job.goal + "\n" + job.context
        task = await self._build_task(job, workflow_messages, lesson)

        result = await reasoner.infer(task=task)

        try:
            result_dict = parse_json(text=result)
        except (ValueError, json.JSONDecodeError) as e:
            # not validated json format
            # color: red
            print(f"\033[38;5;196m[JSON]: {str(e)}\033[0m")
            task.lesson = lesson or "" + (
                "LLM output format (json format for example) specification is crucial for "
                "reliable parsing. And do not forget ```json prefix and ``` suffix when "
                "you generate the json block in <DELIVERABLE>...</DELIVERABLE>. Error info: "
                + str(e)
            )
            result = await reasoner.infer(task=task)
            result_dict = parse_json(text=result)

        return WorkflowMessage(
            payload={
                "scratchpad": workflow_messages[0].scratchpad,
                "status": WorkflowStatus[str(result_dict["status"])],
                "evaluation": result_dict["evaluation"],
                "lesson": result_dict["lesson"],
            }
        )
