from typing import Any, List, Optional

import pytest

from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.job import Job, SubJob
from app.core.model.message import WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.toolkit.tool import Tool
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


class TestReasoner(Reasoner):
    """Test reasoner"""

    def infer(
        self,
        task: Task,
        tools: Optional[List[Tool]] = None,
    ) -> str:
        """Infer by the reasoner."""

    def update_knowledge(self, data: Any) -> None:
        """Update the knowledge."""

    def evaluate(self, data: Any) -> Any:
        """Evaluate the inference process."""

    def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        """Conclude the inference results."""

    def init_memory(self, task: Task) -> ReasonerMemory:
        """Initialize the memory."""

    def get_memory(self, task: Task) -> ReasonerMemory:
        """Get the memory."""


@pytest.fixture
def job():
    """Create a test job."""
    return SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context="Test workflow execution",
    )


@pytest.fixture
def mock_reasoner():
    """Create a mock reasoner."""
    return TestReasoner()


class MockOperator(Operator):
    """Test operator that tracks execution order."""

    def __init__(self, id: str, execution_order: List[str]):
        self._config = OperatorConfig(id=id, instruction="Test instruction", actions=[])
        self._execution_order = execution_order

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        self._execution_order.append(self._config.id)
        return WorkflowMessage(payload={"scratchpad": f"Output from {self._config.id}"})


def test_basic_workflow_execution(job: Job, mock_reasoner: Reasoner):
    """Test basic workflow execution with sequential operators."""
    execution_order = []

    # create operators
    op1 = MockOperator("op1", execution_order)
    op2 = MockOperator("op2", execution_order)

    # create and configure workflow
    workflow = DbgptWorkflow()
    workflow.add_operator(op1)
    workflow.add_operator(op2, previous_ops=[op1])

    # execute workflow
    result = workflow.execute(job=job, reasoner=mock_reasoner)

    # verify execution order
    assert execution_order == ["op1", "op2"]
    assert result.scratchpad == "Output from op2"


def test_parallel_workflow_execution(job: Job, mock_reasoner: Reasoner):
    """Test parallel workflow execution."""
    execution_order = []

    # create operators
    op1 = MockOperator("op1", execution_order)
    op2 = MockOperator("op2", execution_order)
    op3 = MockOperator("op3", execution_order)

    # create workflow with parallel paths
    workflow = DbgptWorkflow()
    workflow.add_operator(op1)
    workflow.add_operator(op2)
    workflow.add_operator(op3, previous_ops=[op1, op2])

    # execute workflow
    result = workflow.execute(job=job, reasoner=mock_reasoner)

    # verify execution
    assert len(execution_order) == 3
    assert execution_order.index("op3") > execution_order.index("op1")
    assert execution_order.index("op3") > execution_order.index("op2")
    assert result.scratchpad == "Output from op3"


def test_workflow_error_handling(job: Job, mock_reasoner: Reasoner):
    """Test workflow error handling."""

    class ErrorOperator(MockOperator):
        """Operator that raises an error during execution."""

        def execute(
            self,
            reasoner: Reasoner,
            job: Job,
            workflow_messages: Optional[List[WorkflowMessage]] = None,
            lesson: Optional[str] = None,
        ) -> WorkflowMessage:
            raise ValueError("Test error")

    # create workflow with error operator
    workflow = DbgptWorkflow()
    workflow.add_operator(ErrorOperator(id="error_op", execution_order=[]))

    # verify error propagation
    with pytest.raises(ValueError, match="Test error"):
        workflow.execute(job=job, reasoner=mock_reasoner)


def test_complex_workflow_topology(job: Job, mock_reasoner: Reasoner):
    """Test complex workflow topology with multiple parallel and sequential paths."""
    execution_order = []

    # create operators
    op1 = MockOperator("op1", execution_order)
    op2 = MockOperator("op2", execution_order)
    op3 = MockOperator("op3", execution_order)
    op4 = MockOperator("op4", execution_order)
    op5 = MockOperator("op5", execution_order)

    # create workflow with complex topology
    workflow = DbgptWorkflow()
    workflow.add_operator(op1)
    workflow.add_operator(op2)
    workflow.add_operator(op3, previous_ops=[op1])
    workflow.add_operator(op4, previous_ops=[op2])
    workflow.add_operator(op5, previous_ops=[op3, op4])

    # execute workflow
    result = workflow.execute(job=job, reasoner=mock_reasoner)

    # verify execution constraints
    assert len(execution_order) == 5
    assert execution_order.index("op3") > execution_order.index("op1")
    assert execution_order.index("op4") > execution_order.index("op2")
    assert execution_order.index("op5") > execution_order.index("op3")
    assert execution_order.index("op5") > execution_order.index("op4")
    assert result.scratchpad == "Output from op5"
