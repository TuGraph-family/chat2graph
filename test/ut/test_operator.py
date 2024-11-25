from typing import List, Tuple
from unittest.mock import AsyncMock

import pytest

from app.agent.reasoner.dual_model import DualModelReasoner
from app.agent.workflow.operator.operator import Operator
from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.tool.tool_resource import Query
from app.toolkit.toolkit import Toolkit


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
    tools = [Query(tool_id=f"{action.id}_tool") for action in actions]

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
async def operator(
    toolkit_setup: Tuple[Toolkit, List[Action], List[Tool]], mock_reasoner: AsyncMock
):
    """Create an operator instance with mock reasoner."""
    toolkit, actions, _ = toolkit_setup
    operator = Operator(
        op_id="test_operator",
        reasoner=mock_reasoner,
        task="Test task",
        toolkit=toolkit,
        actions=[actions[0]],  # start with first action
    )
    await operator.initialize(threshold=0.7, hops=2)
    return operator


@pytest.mark.asyncio
async def test_execute_basic_functionality(
    operator: Operator, mock_reasoner: AsyncMock
):
    """Test basic execution functionality."""
    context = "Test context"
    scratchpad = "Test scratchpad"

    op_output = await operator.execute(
        context=context,
        scratchpad=scratchpad,
        reasoning_rounds=5,
        print_messages=False,
    )

    # verify reasoner.infer was called with correct parameters
    mock_reasoner.infer.assert_called_once()
    call_args = mock_reasoner.infer.call_args[1]

    assert call_args["op_id"] == "test_operator"
    assert "task" in call_args
    assert call_args["reasoning_rounds"] == 5
    assert call_args["print_messages"] is False

    # verify tools were passed correctly
    tools = call_args["func_list"]
    assert len(tools) == 3
    assert all(isinstance(tool, Query) for tool in tools)

    # verify return value
    assert "scratchpad" in op_output
    assert op_output["scratchpad"] == "Test result"


@pytest.mark.asyncio
async def test_execute_custom_prompt_format(operator: Operator):
    """Test that the operation prompt is formatted correctly."""
    context = "Test context"
    scratchpad = "Test scratchpad"

    # get the formatted prompt
    prompt = await operator.format_operation_prompt(
        task=operator._task,
        context=context,
        scratchpad=scratchpad,
    )

    # verify prompt contains all necessary components
    assert operator._task in prompt
    assert context in prompt
    assert scratchpad in prompt


@pytest.mark.asyncio
async def test_execute_with_empty_context(operator: Operator):
    """Test execution with empty context."""
    await operator.execute(
        context="",
        scratchpad="Test scratchpad",
        reasoning_rounds=5,
        print_messages=False,
    )

    # verify reasoner was still called
    operator._reasoner.infer.assert_called_once()


@pytest.mark.asyncio
async def test_execute_with_different_rounds(operator: Operator):
    """Test execution with different numbers of reasoning rounds."""
    test_rounds = 10

    await operator.execute(
        context="Test context",
        scratchpad="Test scratchpad",
        reasoning_rounds=test_rounds,
        print_messages=False,
    )

    # verify correct number of rounds was passed
    call_args = operator._reasoner.infer.call_args[1]
    assert call_args["reasoning_rounds"] == test_rounds


@pytest.mark.asyncio
async def test_get_tools_from_actions(
    operator: Operator, toolkit_setup: Tuple[Toolkit, List[Action], List[Tool]]
):
    """Test tool retrieval from actions."""
    tools = operator.get_tools_from_actions()

    # verify correct number and type of tools
    assert len(tools) == 3
    assert all(isinstance(tool, Query) for tool in tools)

    # verify tool IDs match expected pattern
    expected_tool_ids = {"search_tool", "analyze_tool", "generate_tool"}
    actual_tool_ids = {tool.id for tool in tools}
    assert actual_tool_ids == expected_tool_ids


@pytest.mark.asyncio
async def test_execute_error_handling(operator: Operator):
    """Test error handling during execution."""
    # make reasoner.infer raise an exception
    operator._reasoner.infer.side_effect = Exception("Test error")

    with pytest.raises(Exception) as excinfo:
        await operator.execute(
            context="Test context",
            scratchpad="Test scratchpad",
            reasoning_rounds=5,
            print_messages=False,
        )

    assert str(excinfo.value) == "Test error"
