import asyncio

import matplotlib.pyplot as plt

from app.agent.job import SubJob
from app.agent.reasoner.mono_model_reasoner import MonoModelReasoner
from app.agent.workflow.operator.eval_operator import EvalOperator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.prompt.operator import (
    EVAL_OPERATION_INSTRUCTION_PROMPT,
    EVAL_OPERATION_OUTPUT_PROMPT,
)
from app.common.type import WorkflowStatus
from app.memory.message import WorkflowMessage
from app.toolkit.action.action import Action
from app.toolkit.toolkit import Toolkit, ToolkitService


async def main():
    """Main function to demonstrate Operator usage for the evaluation."""
    # initialize
    toolkit = Toolkit()

    action1 = Action(
        id="action_id_1",
        name="Evaluate",
        description="Evaluate the given result",
    )

    # add actions to toolkit
    toolkit.add_action(action=action1, next_actions=[], prev_actions=[])

    # set operator properties
    reasoner = MonoModelReasoner()
    operator_config = OperatorConfig(
        instruction=EVAL_OPERATION_INSTRUCTION_PROMPT,
        actions=[action1],
        output_schema=EVAL_OPERATION_OUTPUT_PROMPT,
    )

    operator = EvalOperator(config=operator_config, toolkit_service=ToolkitService(toolkit))

    # execute operator (with minimal reasoning rounds for testing)
    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Generate some numbers",
        context="Generate a list of prime numbers between 1 and 20.",
    )
    workflow_message = WorkflowMessage(
        payload={"scratchpad": "[2, 3, 5, 7, 11, 13, 17, 19]"},
    )
    result: WorkflowMessage = await operator.execute(
        reasoner=reasoner,
        job=job,
        workflow_messages=[workflow_message],
    )

    assert result.status == WorkflowStatus.SUCCESS
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
