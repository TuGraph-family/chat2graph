import json
from typing import List, Optional

from app.core.common.async_func import run_async_function
from app.core.common.type import WorkflowStatus
from app.core.common.util import parse_json
from app.core.model.job import Job
from app.core.model.message import WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.workflow.operator import Operator


class EvalOperator(Operator):
    """Operator for evaluating the performance of the model."""

    def execute(
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
        previous_op_message = workflow_messages[0].scratchpad

        task = self._build_task(job, workflow_messages, lesson)

        result = run_async_function(reasoner.infer, task=task)

        try:
            result_dict = parse_json(text=result)
        except (ValueError, json.JSONDecodeError) as e:
            # not validated json format
            # color: red
            print(f"\033[38;5;196m[JSON]: {str(e)}\033[0m")
            task.lesson = lesson or "" + (
                "LLM output format (json format for example) specification is crucial for "
                "reliable parsing. And do not forget ```json prefix and ``` suffix when "
                "you generate the json block in <deliverable>...</deliverable>. Error info: "
                + str(e)
            )
            result = run_async_function(reasoner.infer, task=task)
            result_dict = parse_json(text=result)

        return WorkflowMessage(
            payload={
                "scratchpad": previous_op_message,
                "status": WorkflowStatus[str(result_dict["status"])],
                "evaluation": result_dict["evaluation"],
                "lesson": result_dict["lesson"],
            },
            job_id=job.id,
        )

    def _build_task(
        self, job: Job, workflow_messages: Optional[List[WorkflowMessage]], lesson: Optional[str]
    ) -> Task:
        rec_tools, rec_actions = self._toolkit_service.recommend_tools_actions(
            actions=self._config.actions, threshold=self._config.threshold, hops=self._config.hops
        )

        # refine the workflow messages to help the LLM to evaluate the performance and the process
        workflow_messages_copy: List[WorkflowMessage] = []
        if workflow_messages:
            workflow_messages_copy = [msg.copy() for msg in workflow_messages if msg.scratchpad]
        if len(workflow_messages_copy) == 1:
            workflow_messages_copy[0].scratchpad = (
                "[Job execution result] (and the job does not have the [INPUT INFORMATION], so "
                f"that the evaluation status can not be {WorkflowStatus.INPUT_DATA_ERROR.value}):\n"
                + workflow_messages_copy[0].scratchpad
            )
        elif len(workflow_messages_copy) > 1:
            workflow_messages_copy[0].scratchpad = (
                "[JOB EXECUTION RESULT]:\n" + workflow_messages_copy[0].scratchpad
            )
            for msg in workflow_messages_copy[1:]:
                msg.scratchpad = (
                    "\n[INPUT INFORMATION] (data/conditions/limitations):\n" + msg.scratchpad
                )
        job.context = "[JOB TARGET GOAL]:\n" + job.goal + "\n[INPUT INFORMATION]:\n" + job.context

        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=workflow_messages_copy,
            tools=rec_tools,
            actions=rec_actions,
            knowledge=self.get_knowledge(job),
            insights=self.get_env_insights(),
            lesson=lesson,
        )
        return task
