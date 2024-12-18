from typing import List, Tuple
from unittest.mock import AsyncMock

import pytest

from app.agent.job import Job
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator import Operator
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

    # add actions to toolkit
    toolkit.add_action(
        action=actions[0], next_actions=[(actions[1], 0.9)], prev_actions=[]
    )
    toolkit.add_action(
        action=actions[1],
        next_actions=[(actions[2], 0.8)],
        prev_actions=[(actions[0], 0.9)],
    )
    toolkit.add_action(
        action=actions[2], next_actions=[], prev_actions=[(actions[1], 0.8)]
    )

    # add tools to toolkit
    for tool, action in zip(tools, actions):
        toolkit.add_tool(tool=tool, connected_actions=[(action, 0.9)])

    return toolkit, actions, tools


@pytest.fixture
def mock_reasoner():
    """Create a mock reasoner."""
    reasoner = AsyncMock(spec=DualModelReasoner)
    reasoner.infer = AsyncMock()
    reasoner.infer.return_value = "Test result"
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
    operator = Operator(config=config, toolkit_service=ToolkitService(toolkit=toolkit))
    return operator


@pytest.mark.asyncio
async def test_execute_basic_functionality(
    operator: Operator, mock_reasoner: AsyncMock
):
    """Test basic execution functionality."""
    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )
    workflow_message = WorkflowMessage(content={"scratchpad": "Test scratchpad"})

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
    tools = task.tools
    assert len(tools) == 3
    assert all(isinstance(tool, Query) for tool in tools)

    # verify return value
    assert isinstance(op_output, WorkflowMessage)
    assert str(op_output.scratchpad) == "Test result"


@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_get_tools_from_actions(
    operator: Operator, toolkit_setup: Tuple[Toolkit, List[Action], List[Tool]]
):
    """Test tool retrieval from actions."""
    tools = await operator.get_tools_from_actions()

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

    job = Job(
        id="test_job_id",
        session_id="test_session_id",
        goal="Test goal",
    )
    workflow_message = WorkflowMessage(content={"scratchpad": "Test scratchpad"})

    with pytest.raises(Exception) as excinfo:
        await operator.execute(
            reasoner=mock_reasoner,
            workflow_messages=[workflow_message],
            job=job,
        )

    assert str(excinfo.value) == "Test error"


@pytest.mark.asyncio
async def test_get_tools_from_actions_duplicates(
    operator: Operator, toolkit_setup: Tuple[Toolkit, List[Action], List[Tool]]
):
    """Test tool retrieval handles duplicates correctly."""
    # add duplicate tools to actions
    _, _, tools = toolkit_setup
    for action in operator._config.actions:
        action.tools = tools  # Deliberately add all tools to each action

    operator._config.threshold = 0.7
    operator._config.hops = 1
    retrieved_tools = await operator.get_tools_from_actions()

    # verify no duplicates
    tool_ids = [tool.id for tool in retrieved_tools]
    assert len(tool_ids) == len(set(tool_ids))
