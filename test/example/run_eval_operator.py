import asyncio

import matplotlib.pyplot as plt

from app.core.common.type import WorkflowStatus
from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage
from app.core.prompt.operator import (
    EVAL_OPERATION_INSTRUCTION_PROMPT,
    EVAL_OPERATION_OUTPUT_PROMPT,
)
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.workflow.eval_operator import EvalOperator
from app.core.workflow.operator_config import OperatorConfig


async def main():
    """Main function to demonstrate Operator usage for the evaluation."""
    # initialize
    action1 = Action(
        id="action_id_1",
        name="Evaluate",
        description="Evaluate the given result",
    )

    # set operator properties
    reasoner = MonoModelReasoner()
    operator_config = OperatorConfig(
        instruction=EVAL_OPERATION_INSTRUCTION_PROMPT,
        actions=[action1],
        output_schema=EVAL_OPERATION_OUTPUT_PROMPT,
    )

    operator = EvalOperator(config=operator_config)

    # add actions to toolkit
    toolkit_service: ToolkitService = ToolkitService.instance or ToolkitService()
    toolkit_service.add_action(
        id=operator.get_id(), action=action1, next_actions=[], prev_actions=[]
    )

    # execute operator (with minimal reasoning rounds for testing)
    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Generate some numbers",
        context="Generate a list of prime numbers given the start and end values.",
    )
    execution_message = WorkflowMessage(
        payload={
            "scratchpad": "After the generation, the result is [2, 3, 5, 7, 11, 13, 17, 19, 23, 24]"
        },
    )
    input_message_1 = WorkflowMessage(
        payload={"scratchpad": "The start value is 1."},
    )
    input_message_2 = WorkflowMessage(
        payload={"scratchpad": "The end value is 21."},
    )
    result: WorkflowMessage = await operator.execute(
        reasoner=reasoner,
        job=job,
        workflow_messages=[execution_message, input_message_1, input_message_2],
    )

    assert result.status == WorkflowStatus.EXECUTION_ERROR
    assert result.evaluation
    assert result.scratchpad
    print(
        f"Operator execution result:\nstaus: {result.status}\n"
        f"evaluation: {result.evaluation}\n"
        f"lesson: {result.lesson}\n"
        f"scratchpad: {result.scratchpad}"
    )
    print("Operator execution completed successfully")

    plt.show()


if __name__ == "__main__":
    asyncio.run(main())
