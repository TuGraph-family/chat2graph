from typing import List, Tuple
from unittest.mock import AsyncMock

import pytest

from app.agent.job import SubJob
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.eval_operator import EvalOperator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.memory.message import WorkflowMessage
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.tool.tool_resource import Query
from app.toolkit.toolkit import Toolkit, ToolkitService


@pytest.fixture
def toolkit_setup():
    """Setup a toolkit with actions and tools."""
    toolkit = Toolkit()

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
    tools = [Query(id=f"{action.id}_tool") for action in actions]

    # add actions to toolkit
    toolkit.add_action(action=actions[0], next_actions=[(actions[1], 0.9)], prev_actions=[])
    toolkit.add_action(action=actions[1], next_actions=[], prev_actions=[(actions[0], 0.9)])

    # add tools to toolkit
    for tool, action in zip(tools, actions, strict=False):
        toolkit.add_tool(tool=tool, connected_actions=[(action, 0.9)])

    return toolkit, actions, tools


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
async def operator(toolkit_setup: Tuple[Toolkit, List[Action], List[Tool]]):
    """Create an operator instance with mock reasoner."""
    toolkit, actions, _ = toolkit_setup
    config = OperatorConfig(
        instruction="Test instruction",
        actions=[actions[0]],  # start with first action
        threshold=0.7,
        hops=2,
    )
    return EvalOperator(config=config, toolkit_service=ToolkitService(toolkit=toolkit))


@pytest.mark.asyncio
async def test_execute_basic_functionality(operator: EvalOperator, mock_reasoner: AsyncMock):
    """Test basic execution functionality."""
    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )
    workflow_message = WorkflowMessage(payload={"scratchpad": "[2, 3, 5, 7, 11, 13, 17, 19]"})

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
    assert all(isinstance(tool, Query) for tool in task.tools)

    # verify return value
    assert isinstance(op_output, WorkflowMessage)
    assert str(op_output.scratchpad) == "[2, 3, 5, 7, 11, 13, 17, 19]"


@pytest.mark.asyncio
async def test_execute_error_handling(operator: EvalOperator, mock_reasoner: AsyncMock):
    """Test error handling during execution."""
    # make reasoner.infer raise an exception
    mock_reasoner.infer.side_effect = Exception("Test error")

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
    )
    workflow_message = WorkflowMessage(payload={"scratchpad": "[2, 3, 5, 7, 11, 13, 17, 19]"})

    with pytest.raises(Exception) as excinfo:
        await operator.execute(
            reasoner=mock_reasoner,
            workflow_messages=[workflow_message],
            job=job,
        )

    assert str(excinfo.value) == "Test error"
