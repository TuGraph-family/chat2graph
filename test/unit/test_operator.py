from unittest.mock import AsyncMock

import pytest

from app.core.model.job import SubJob
from app.core.model.message import WorkflowMessage
from app.core.model.task import Task
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from test.resource.tool_resource import Query


@pytest.fixture
def mock_reasoner():
    """Create a mock reasoner."""
    reasoner = AsyncMock(spec=DualModelReasoner)
    reasoner.infer = AsyncMock()
    reasoner.infer.return_value = "Test result"
    return reasoner


@pytest.fixture
async def operator():
    """Create an operator instance with mock reasoner."""
    toolkit_service = ToolkitService()

    # create actions
    actions = [
        Action(
            id="search",
            name="Search Knowledge",
            description="Search relevant information from knowledge base",
        ),
        Action(
            id="analyze",
            name="Analyze Content",
            description="Analyze and extract insights from content",
        ),
        Action(
            id="generate",
            name="Generate Response",
            description="Generate response based on analysis",
        ),
    ]

    # create tools
    tools = [Query(id=f"{action.id}_tool") for action in actions]

    config = OperatorConfig(
        instruction="Test instruction",
        actions=[actions[0]],  # start with first action
        threshold=0.7,
        hops=2,
    )
    operator = Operator(config=config)

    # add actions to toolkit
    toolkit_service.add_action(action=actions[0], next_actions=[(actions[1], 0.9)], prev_actions=[])
    toolkit_service.add_action(
        action=actions[1], next_actions=[(actions[2], 0.8)], prev_actions=[(actions[0], 0.9)]
    )
    toolkit_service.add_action(action=actions[2], next_actions=[], prev_actions=[(actions[1], 0.8)])

    # add tools to toolkit
    for tool, action in zip(tools, actions, strict=False):
        toolkit_service.add_tool(tool=tool, connected_actions=[(action, 0.9)])

    return operator


@pytest.mark.asyncio
async def test_execute_basic_functionality(operator: Operator, mock_reasoner: AsyncMock):
    """Test basic execution functionality."""
    job = SubJob(
        id="test_job_id", session_id="test_session_id", goal="Test goal", context="Test context"
    )
    workflow_message = WorkflowMessage(payload={"scratchpad": "Test scratchpad"}, job_id=job.id)

    op_output = operator.execute(
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
    assert len(actions) == 3
    assert all(isinstance(tool, Query) for tool in task.tools)

    # verify return value
    assert isinstance(op_output, WorkflowMessage)
    assert str(op_output.scratchpad) == "Test result"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_get_tools_from_actions(operator: Operator):
    """Test tool retrieval from actions."""
    toolkit_service: ToolkitService = ToolkitService.instance
    tools, _ = toolkit_service.recommend_tools_actions(
        actions=operator._config.actions,
        threshold=operator._config.threshold,
        hops=operator._config.hops,
    )

    # verify correct number and type of tools
    assert len(tools) == 3
    assert all(isinstance(tool, Query) for tool in tools)

    # verify tool IDs match expected pattern
    expected_tool_ids = {"search_tool", "analyze_tool", "generate_tool"}
    actual_tool_ids = {tool.id for tool in tools}
    assert actual_tool_ids == expected_tool_ids


@pytest.mark.asyncio
async def test_execute_error_handling(operator: Operator, mock_reasoner: AsyncMock):
    """Test error handling during execution."""
    # make reasoner.infer raise an exception
    mock_reasoner.infer.side_effect = Exception("Test error")

    job = SubJob(id="test_job_id", session_id="test_session_id", goal="Test goal")
    workflow_message = WorkflowMessage(payload={"scratchpad": "Test scratchpad"}, job_id=job.id)

    with pytest.raises(Exception) as excinfo:
        operator.execute(reasoner=mock_reasoner, workflow_messages=[workflow_message], job=job)

    assert str(excinfo.value) == "Test error"
