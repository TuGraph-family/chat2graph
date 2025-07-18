from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.workflow.eval_operator import EvalOperator
from app.core.workflow.operator_config import OperatorConfig
from test.resource.init_server import init_server
from test.resource.tool_resource import ExampleQuery

init_server()


@pytest.fixture
def mock_reasoner():
    """Create a mock reasoner."""
    reasoner = AsyncMock(spec=DualModelReasoner)
    reasoner.infer = AsyncMock()
    reasoner.infer.return_value = """
    ```json
    {
        "status": "SUCCESS",
        "evaluation": "The content is evaluated and analyzed successfully.",
        "lesson": "The consistance of the prime numbers is the key to the success."
    }
    ``` 
"""  # noqa: E501
    return reasoner


@pytest.fixture
async def operator():
    """Create an operator instance with mock reasoner."""
    toolkit_service = ToolkitService()

    # create actions
    actions = [
        Action(
            id="evaluate_content",
            name="Content Evaluation",
            description="Evaluate and analyze input content and extracting insights",
        ),
        Action(
            id="evaluate_response",
            name="Response Evaluation",
            description="Generate and evaluate response quality based on content analysis",
        ),
    ]

    # create tools
    tools = [ExampleQuery() for _ in actions]

    config = OperatorConfig(
        instruction="Test instruction",
        actions=[actions[0]],  # start with first action
        threshold=0.7,
        hops=2,
    )
    eval_operator = EvalOperator(config=config)

    # add actions to toolkit
    toolkit_service.add_action(action=actions[0], next_actions=[(actions[1], 0.9)], prev_actions=[])
    toolkit_service.add_action(action=actions[1], next_actions=[], prev_actions=[(actions[0], 0.9)])
    # add tools to toolkit
    for tool, action in zip(tools, actions, strict=False):
        toolkit_service.add_tool(tool=tool, connected_actions=[(action, 0.9)])
    return eval_operator


@pytest.mark.asyncio
async def test_execute_basic_functionality(operator: EvalOperator, mock_reasoner: AsyncMock):
    """Test basic execution functionality."""
    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )
    workflow_message = WorkflowMessage(
        payload={"scratchpad": "[2, 3, 5, 7, 11, 13, 17, 19]"}, job_id=job.id
    )

    op_output = await operator.execute(
        reasoner=mock_reasoner,
        workflow_messages=[workflow_message],
        job=job,
    )

    # verify reasoner.infer was called with correct parameters
    mock_reasoner.infer.assert_called_once()
    call_args = mock_reasoner.infer.call_args[1]

    assert "task" in call_args

    # verify tools were passed correctly
    task: Task = call_args["task"]
    actions = task.actions
    assert len(actions) == 2
    assert all(isinstance(tool, ExampleQuery) for tool in task.tools)

    # verify return value
    assert isinstance(op_output, WorkflowMessage)
    assert str(op_output.scratchpad) == "[2, 3, 5, 7, 11, 13, 17, 19]"


@pytest.mark.asyncio
async def test_execute_error_handling(operator: EvalOperator, mock_reasoner: AsyncMock):
    """Test error handling during execution."""
    # make reasoner.infer raise an exception
    mock_reasoner.infer.side_effect = Exception("Test error")

    job = SubJob(id="test_job_id" + str(uuid4()), session_id="test_session_id", goal="Test goal")
    workflow_message = WorkflowMessage(
        payload={"scratchpad": "[2, 3, 5, 7, 11, 13, 17, 19]"}, job_id=job.id
    )

    with pytest.raises(Exception) as excinfo:
        await operator.execute(
            reasoner=mock_reasoner, workflow_messages=[workflow_message], job=job
        )

    assert str(excinfo.value) == "Test error"
