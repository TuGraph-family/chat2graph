from unittest import mock

import pytest

# Assuming these imports are correct for your project structure
from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool_config import ToolGroupConfig
from app.core.toolkit.tool_group import ToolPackage
from test.resource.tool_resource import ExampleQuery

# Initialize the singleton service instance for tests
ToolkitService()


# --- Helper function to create mocks for clarity ---
def mock_toolkit_service(mocker):
    """Mocks all relevant methods of ToolkitService."""
    mock_add_action = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_action",
        new_callable=mock.Mock,
    )
    mock_add_tool = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_tool",
        new_callable=mock.Mock,
    )
    mock_add_tool_group = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_tool_group",
        new_callable=mock.Mock,
    )
    return mock_add_action, mock_add_tool, mock_add_tool_group


# --- Tests that remain largely unchanged (but updated for clarity) ---


def test_chain_single_action(mocker):
    """Test the chain method with a single action."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, _ = mock_toolkit_service(mocker)

    action = Action(id="test_action_id", name="action", description="test_description")

    wrapper.chain(action)

    # The first action has no preceding actions.
    mock_add_action.assert_called_once_with(action, next_actions=[], prev_actions=[])
    mock_add_tool.assert_not_called()


def test_chain_action_and_tool(mocker):
    """Test the chain method with action followed by tool."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, _ = mock_toolkit_service(mocker)

    tool = ExampleQuery()
    tool._id = "test_tool_id"
    action = Action(id="test_action_id", name="action", description="test_description")

    wrapper.chain(action, tool)

    # Action is added first with no connections yet.
    mock_add_action.assert_called_once_with(action, next_actions=[], prev_actions=[])
    # Tool is connected to the preceding action.
    mock_add_tool.assert_called_once_with(tool, connected_actions=[(action, 1.0)])


def test_chain_action_and_tool_group(mocker):
    """Test the chain method with action followed by tool group."""
    wrapper = ToolkitWrapper()
    mock_add_action, _, mock_add_tool_group = mock_toolkit_service(mocker)

    tool_group = ToolPackage(ToolGroupConfig(type="package", name="test_package"))
    action = Action(id="test_action_id", name="action", description="test_description")

    wrapper.chain(action, tool_group)

    mock_add_action.assert_called_once_with(action, next_actions=[], prev_actions=[])
    mock_add_tool_group.assert_called_once_with(tool_group, connected_actions=[(action, 1.0)])


# --- Tests that required significant changes ---


def test_chain_multiple_actions(mocker):
    """Test the chain method with multiple actions in sequence."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, _ = mock_toolkit_service(mocker)

    action1 = Action(id="action_1", name="action_1", description="desc1")
    action2 = Action(id="action_2", name="action_2", description="desc2")

    wrapper.chain(action1, action2)

    assert mock_add_action.call_count == 2
    mock_add_tool.assert_not_called()

    # Expected calls based on the new logic (each action connects to its predecessor)
    expected_calls = [
        # First action has no predecessor
        mock.call(action1, next_actions=[], prev_actions=[]),
        # Second action is connected to the first one
        mock.call(action2, next_actions=[], prev_actions=[(action1, 1.0)]),
    ]
    mock_add_action.assert_has_calls(expected_calls, any_order=False)


def test_chain_with_tuple(mocker):
    """Test the chain method with tuple starting with action (sequential chain)."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, _ = mock_toolkit_service(mocker)

    tool1 = ExampleQuery()
    tool1._id = "tool_1"
    action1 = Action(id="action_1", name="action_1", description="desc1")
    action2 = Action(id="action_2", name="action_2", description="desc2")

    # The tuple (action1, tool1) is flattened into the main chain.
    wrapper.chain((action1, tool1), action2)

    # Check calls in order
    add_action_calls = [
        mock.call(action1, next_actions=[], prev_actions=[]),
        mock.call(action2, next_actions=[], prev_actions=[(action1, 1.0)]),
    ]
    mock_add_action.assert_has_calls(add_action_calls, any_order=False)
    assert mock_add_action.call_count == 2

    # Tool1 is connected to action1, which precedes it in the flattened chain.
    mock_add_tool.assert_called_once_with(tool1, connected_actions=[(action1, 1.0)])


def test_chain_with_parallel_tools(mocker):
    """Test the chain method with action followed by parallel tools."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, _ = mock_toolkit_service(mocker)

    action1 = Action(id="action_1", name="action_1", description="desc1")
    tool1 = ExampleQuery()
    tool1._id = "tool_1"
    tool2 = ExampleQuery()
    tool2._id = "tool_2"

    wrapper.chain(action1, (tool1, tool2))

    mock_add_action.assert_called_once_with(action1, next_actions=[], prev_actions=[])

    # Both tools in the parallel tuple should be connected to action1
    add_tool_calls = [
        mock.call(tool1, connected_actions=[(action1, 1.0)]),
        mock.call(tool2, connected_actions=[(action1, 1.0)]),
    ]
    mock_add_tool.assert_has_calls(add_tool_calls, any_order=True)
    assert mock_add_tool.call_count == 2


# --- Invalid pattern tests (should pass without changes) ---


def test_chain_invalid_tool_first(mocker):
    """Test that chain raises error when starting with tool."""
    wrapper = ToolkitWrapper()
    tool = ExampleQuery()
    tool._id = "test_tool_id"
    with pytest.raises(ValueError, match="Chain must start with an Action"):
        wrapper.chain(tool)


def test_chain_invalid_tool_group_first(mocker):
    """Test that chain raises error when starting with tool group."""
    wrapper = ToolkitWrapper()
    tool_group = ToolPackage(ToolGroupConfig(type="package", name="test_package"))
    with pytest.raises(ValueError, match="Chain must start with an Action"):
        wrapper.chain(tool_group)


def test_chain_invalid_tool_followed_by_tool(mocker):
    """Test that chain raises error when tool is followed by tool."""
    wrapper = ToolkitWrapper()
    action = Action(id="action_1", name="action_1", description="desc1")
    tool1 = ExampleQuery()
    tool1._id = "tool_1"
    tool2 = ExampleQuery()
    tool2._id = "tool_2"
    # The error message is general enough to still match
    with pytest.raises(ValueError, match="can only be followed by an Action"):
        wrapper.chain(action, tool1, tool2)


def test_chain_invalid_parallel_with_action(mocker):
    """Test that chain raises error when parallel tuple contains action."""
    wrapper = ToolkitWrapper()
    action1 = Action(id="action_1", name="action_1", description="desc1")
    action2 = Action(id="action_2", name="action_2", description="desc2")
    tool = ExampleQuery()
    tool._id = "tool_1"
    # The error message is general enough to still match
    with pytest.raises(
        ValueError, match="Parallel connection tuples can only contain Tools or ToolGroups"
    ):
        wrapper.chain(action1, (tool, action2))


# --- Complex/Mixed tests ---


def test_chain_with_mixed_items(mocker):
    """Test the chain method with mixed actions, tools, and tool groups."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, mock_add_tool_group = mock_toolkit_service(mocker)

    action1 = Action(id="action_1", name="action_1", description="desc1")
    tool = ExampleQuery()
    tool._id = "test_tool_id"
    action2 = Action(id="action_2", name="action_2", description="desc2")
    tool_group = ToolPackage(ToolGroupConfig(type="package", name="test_package"))

    wrapper.chain(action1, tool, action2, tool_group)

    # Check action calls
    add_action_calls = [
        mock.call(action1, next_actions=[], prev_actions=[]),
        mock.call(action2, next_actions=[], prev_actions=[(action1, 1.0)]),
    ]
    mock_add_action.assert_has_calls(add_action_calls, any_order=False)
    assert mock_add_action.call_count == 2

    # Check tool and tool group calls
    mock_add_tool.assert_called_once_with(tool, connected_actions=[(action1, 1.0)])
    mock_add_tool_group.assert_called_once_with(tool_group, connected_actions=[(action2, 1.0)])


def test_chain_with_tuple_including_tool_group(mocker):
    """Test the chain method with tuple containing tool group."""
    wrapper = ToolkitWrapper()
    mock_add_action, _, mock_add_tool_group = mock_toolkit_service(mocker)

    action1 = Action(id="action_1", name="action_1", description="desc1")
    tool_group1 = ToolPackage(ToolGroupConfig(type="package", name="test_package1"))
    tool_group2 = ToolPackage(ToolGroupConfig(type="package", name="test_package2"))

    wrapper.chain(action1, (tool_group1, tool_group2))

    mock_add_action.assert_called_once_with(action1, next_actions=[], prev_actions=[])

    add_tool_group_calls = [
        mock.call(tool_group1, connected_actions=[(action1, 1.0)]),
        mock.call(tool_group2, connected_actions=[(action1, 1.0)]),
    ]
    mock_add_tool_group.assert_has_calls(add_tool_group_calls, any_order=True)
    assert mock_add_tool_group.call_count == 2


# --- New test for complex chain (Action -> Tuple -> Action) ---


def test_chain_complex_parallel_and_sequential(mocker):
    """Test a complex chain with parallel tools followed by another action."""
    wrapper = ToolkitWrapper()
    mock_add_action, mock_add_tool, mock_add_tool_group = mock_toolkit_service(mocker)

    action1 = Action(id="action_1", name="action_1", description="desc1")
    tool1 = ExampleQuery()
    tool1._id = "tool_1"
    tool_group1 = ToolPackage(ToolGroupConfig(type="package", name="test_package1"))
    action2 = Action(id="action_2", name="action_2", description="desc2")
    tool2 = ExampleQuery()
    tool2._id = "tool_2"

    # This chain was invalid in the old logic but is now valid and crucial to test.
    wrapper.chain(action1, (tool1, tool_group1), action2, tool2)

    # 1. Check action calls
    add_action_calls = [
        mock.call(action1, next_actions=[], prev_actions=[]),
        # action2 should connect to action1, skipping over the tuple
        mock.call(action2, next_actions=[], prev_actions=[(action1, 1.0)]),
    ]
    mock_add_action.assert_has_calls(add_action_calls, any_order=False)
    assert mock_add_action.call_count == 2

    # 2. Check tool calls
    add_tool_calls = [
        # tool1 is in the tuple, connected to action1
        mock.call(tool1, connected_actions=[(action1, 1.0)]),
        # tool2 is at the end, connected to action2
        mock.call(tool2, connected_actions=[(action2, 1.0)]),
    ]
    mock_add_tool.assert_has_calls(add_tool_calls, any_order=True)
    assert mock_add_tool.call_count == 2

    # 3. Check tool group call
    mock_add_tool_group.assert_called_once_with(tool_group1, connected_actions=[(action1, 1.0)])
