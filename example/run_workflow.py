import asyncio
import time
from typing import Any, List, Optional

from app.agent.job import Job, SubJob
from app.agent.reasoner.reasoner import Reasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.type import WorkflowStatus
from app.memory.message import WorkflowMessage
from app.memory.reasoner_memory import BuiltinReasonerMemory, ReasonerMemory
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.toolkit.tool.tool import Tool


class TestReasoner(Reasoner):
    """Test reasoner"""

    async def infer(
        self,
        task: Task,
        tools: Optional[List[Tool]] = None,
    ) -> str:
        """Infer by the reasoner."""
        return "Test inference"

    async def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    async def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    async def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclude the inference results."""
        return "Test conclusion"

    def init_memory(self, task: Task) -> ReasonerMemory:
        """Initialize the memory."""
        return BuiltinReasonerMemory()

    def get_memory(self, task: Task) -> ReasonerMemory:
        """Get the memory."""
        return BuiltinReasonerMemory()


class BaseTestOperator(Operator):
    """Base test operator"""

    def __init__(self, id: str):
        # TODO: Call super().__init__(), but here we just want to show the usage of the workflow
        self._config = OperatorConfig(
            id=id,
            instruction="Test instruction",
            actions=[],
        )

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        raise NotImplementedError


class UpperOperator(BaseTestOperator):
    """Upper operator"""

    def __init__(self, id: str):
        super().__init__(id=id)

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        scratchpad_content = ""
        if workflow_messages:
            scratchpad_content = ""
            for workflow_message in workflow_messages:
                scratchpad_content += workflow_message.scratchpad
        result = job.context.upper() + scratchpad_content.upper()
        print(f"UpperOperator input - context: {job.context}, scratchpad: {scratchpad_content}")
        print(f"UpperOperator output: {result}\n\n")
        return WorkflowMessage(payload={"scratchpad": result})


class AddPrefixOperator(BaseTestOperator):
    """Add prefix operator"""

    def __init__(self, id: str):
        super().__init__(id=id)

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        # to avoid the async issue of UpperOperator
        time.sleep(1)

        scratchpad_content = ""
        if workflow_messages:
            for workflow_message in workflow_messages:
                scratchpad_content += workflow_message.scratchpad

        result = f"Prefix_{scratchpad_content}{job.context}"
        print(f"AddPrefixOperator input - context: {job.context}, scratchpad: {scratchpad_content}")
        print(f"AddPrefixOperator output: {result}\n\n")
        return WorkflowMessage(payload={"scratchpad": result})


class AddSuffixOperator(BaseTestOperator):
    """Add suffix operator"""

    def __init__(self, id: str):
        super().__init__(id=id)

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        scratchpad_content = ""
        if workflow_messages:
            for workflow_message in workflow_messages:
                scratchpad_content += workflow_message.scratchpad

        result = f"{scratchpad_content}_Suffix"
        print(f"AddSuffixOperator input - context: {job.context}, scratchpad: {scratchpad_content}")
        print(f"AddSuffixOperator output: {result}\n\n")
        return WorkflowMessage(payload={"scratchpad": result})


class EvalOperator(BaseTestOperator):
    """Eval operator"""

    def __init__(self, id: str):
        super().__init__(id=id)

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        scratchpad_content = ""
        if workflow_messages:
            for workflow_message in workflow_messages:
                scratchpad_content += workflow_message.scratchpad
        assert (
            scratchpad_content
            == "WE ARE TESTING PARALLEL WORKFLOWPrefix_We are testing parallel workflow_Suffix"
        )
        result = f"Eval_{scratchpad_content}"
        print(f"EvalOperator input - context: {job.context}, scratchpad: {scratchpad_content}")
        print(f"EvalOperator output: {result}\n\n")
        return WorkflowMessage(
            payload={
                "scratchpad": result,
                "status": "success",
                "experience": "The workflow is executed successfully",
            }
        )


async def main():
    """Test parallel workflow: Upper -> Join <- Prefix"""
    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context="We are testing parallel workflow",
    )

    op1 = UpperOperator(id="upper_op")
    op2 = AddPrefixOperator(id="prefix_op")
    op3 = AddSuffixOperator(id="merge_op")
    eval_operator = EvalOperator(id="eval_op")

    workflow = DbgptWorkflow()
    workflow.add_operator(op1)
    workflow.add_operator(op2)
    workflow.add_operator(op3, previous_ops=[op1, op2])
    workflow.set_evaluator(eval_operator)

    result: WorkflowMessage = await workflow.execute(job=job, reasoner=TestReasoner())
    print(f"Final result: {result.scratchpad}")

    assert result.status == WorkflowStatus.SUCCESS.value
    assert (
        result.scratchpad
        == "Eval_WE ARE TESTING PARALLEL WORKFLOWPrefix_We are testing parallel workflow_Suffix"
    )


if __name__ == "__main__":
    asyncio.run(main())
