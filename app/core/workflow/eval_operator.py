import json
from typing import List, Optional

from app.core.common.type import WorkflowStatus
from app.core.common.util import parse_jsons
from app.core.model.job import Job
from app.core.model.message import WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.service.toolkit_service import ToolkitService
from app.core.workflow.operator import Operator


class EvalOperator(Operator):
    """Operator for evaluating the performance of the model."""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the operator by LLM client.

        In this operator, the LLM client will evaluate the performance of the workflow outputs

        Args:
            reasoner (Reasoner): The reasoner.
            job (Job): The job assigned to the expert.
            workflow_messages (Optional[List[WorkflowMessage]]): The outputs of previous operators.
            previous_expert_outputs (Optional[List[WorkflowMessage]]): The outputs of previous
                experts in workflow message type.
            lesson (Optional[str]): The lesson learned (provided by the successor expert).
        """
        assert workflow_messages is not None and len(workflow_messages) == 1, (
            "There should be only one tail operator in the workflow, "
            "so that the length of the workflow messages should be 1."
        )
        # assume the there is only one tail operator in the workflow, so the first workflow message
        # is the output of the evaluated operator
        previous_op_message = workflow_messages[0].scratchpad

        task = self._build_task(
            job=job,
            workflow_messages=workflow_messages,
            previous_expert_outputs=previous_expert_outputs,
            lesson=lesson,
        )

        result = await reasoner.infer(task=task)

        try:
            parse_result = parse_jsons(text=result)[0]
            if isinstance(parse_result, json.JSONDecodeError):
                raise parse_result
            result_dict = parse_result
        except (ValueError, json.JSONDecodeError) as e:
            # not validated json format
            # color: red
            print(f"\033[38;5;196m[JSON]: {str(e)}\033[0m")
            task.lesson = lesson or "" + (
                "LLM output format (json format) specification is crucial for "
                "reliable parsing. And do not forget ```json prefix and ``` suffix when "
                "you generate the json block in <deliverable>...</deliverable>. Error info: "
                + str(e)
            )
            result = await reasoner.infer(task=task)
            parse_result = parse_jsons(text=result)[0]
            if isinstance(parse_result, json.JSONDecodeError):
                raise parse_result from e
            result_dict = parse_result

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
        self,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> Task:
        toolkit_service: ToolkitService = ToolkitService.instance

        rec_tools, rec_actions = toolkit_service.recommend_tools_actions(
            actions=self._config.actions,
            threshold=self._config.threshold,
            hops=self._config.hops,
        )

        assert workflow_messages is not None and len(workflow_messages) == 1, (
            "There should be only one tail operator in the workflow, "
            "so that the length of the workflow messages should be 1."
        )

        # refine the workflow messages to help the LLM to evaluate the performance and the process.
        # if there is no previous expert outputs, the evaluation status must not be
        # INPUT_DATA_ERROR, because there is no previous expert.
        # if there are previous expert outputs, it will refine the workflow messages to help the
        # evaluator to better understand the process and the prompt.
        merged_workflow_messages: List[WorkflowMessage] = []
        workflow_message_copy = workflow_messages[0].copy()
        if not previous_expert_outputs:
            workflow_message_copy.scratchpad = (
                f"[JOB EXECUTION RESULT]:\n{workflow_message_copy.scratchpad}\n"
                "[JOB INPUT INFORMATION] (data/conditions/limitations):\n"
                "The execution does not need the input information. So the evaluation status must "
                f"not be `{WorkflowStatus.INPUT_DATA_ERROR.value}` in this special case!!!"
            )
            merged_workflow_messages = [workflow_message_copy]
        else:
            workflow_message_copy.scratchpad = (
                "[JOB EXECUTION RESULT]:\n" + workflow_message_copy.scratchpad
            )
            merged_workflow_messages = [workflow_message_copy]

            previous_expert_outputs_copy: List[WorkflowMessage] = [
                msg.copy() for msg in previous_expert_outputs
            ]
            for msg in previous_expert_outputs_copy:
                msg.scratchpad = (
                    "\n[JOB INPUT INFORMATION] (data/conditions/limitations):\n" + msg.scratchpad
                )
            merged_workflow_messages.extend(previous_expert_outputs_copy)

        task = Task(
            job=job,
            operator_config=self._config,
            workflow_messages=merged_workflow_messages,
            tools=rec_tools,
            actions=rec_actions,
            knowledge=self.get_knowledge(job),
            insights=self.get_env_insights(),
            lesson=lesson,
        )
        return task
