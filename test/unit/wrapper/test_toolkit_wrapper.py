from unittest import mock

from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from test.resource.tool_resource import ExampleQuery

ToolkitService()


def test_chain_single_action(mocker):
    """Test the chain method with a single action."""
    wrapper = ToolkitWrapper()

    mock_add_action_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_action",
        new_callable=mock.Mock,
    )
    mock_add_tool_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_tool",
        new_callable=mock.Mock,
    )

    action = Action(
        id="test_action_id",
        name="action",
        description="test_description",
        tools=[],
    )

    # call the chain method with a single action
    wrapper.chain(action)

    # check the add_action method was called once
    mock_add_action_method.assert_called_once_with(action, [], [])

    # check the add_tool method was not called
    mock_add_tool_method.assert_not_called()


def test_chain_action_and_tool(mocker):
    """Test the chain method with action followed by tool."""
    wrapper = ToolkitWrapper()

    mock_add_action_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_action",
        new_callable=mock.Mock,
    )
    mock_add_tool_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_tool",
        new_callable=mock.Mock,
    )

    tool = ExampleQuery()
    tool._id = "test_tool_id"
    action = Action(
        id="test_action_id",
        name="action",
        description="test_description",
        tools=[],
    )

    # call the chain method with action followed by tool
    wrapper.chain(action, tool)

    # check the add_action method was called once
    mock_add_action_method.assert_called_once_with(action, [], [])

    # check the add_tool method was called once with connection to action
    mock_add_tool_method.assert_called_once_with(tool, connected_actions=[(action, 1.0)])


def test_chain_multiple_actions(mocker):
    """Test the chain method with multiple actions in sequence."""
    wrapper = ToolkitWrapper()

    mock_add_action_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_action",
        new_callable=mock.Mock,
    )
    mock_add_tool_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_tool",
        new_callable=mock.Mock,
    )

    action1 = Action(
        id="action_1",
        name="action_1",
        description="action_description_1",
        tools=[],
    )
    action2 = Action(
        id="action_2",
        name="action_2",
        description="action_description_2",
        tools=[],
    )

    # call the chain method with two actions
    wrapper.chain(action1, action2)

    # check the add_action method was called twice
    assert mock_add_action_method.call_count == 2

    # check the add_action method was called with action1 (first call)
    action1_call_args = mock_add_action_method.call_args_list[0]
    action1_arg_add_action = action1_call_args[0][0]
    assert action1_arg_add_action.id == "action_1"
    next_actions_arg_action1 = action1_call_args[0][1]
    assert len(next_actions_arg_action1) == 1
    next_action, score = next_actions_arg_action1[0]
    assert next_action.id == "action_2"
    assert score == 1.0
    prev_actions_arg_action1 = action1_call_args[0][2]
    assert prev_actions_arg_action1 == []

    # check the add_action method was called with action2 (second call)
    action2_call_args = mock_add_action_method.call_args_list[1]
    action2_arg_add_action = action2_call_args[0][0]
    assert action2_arg_add_action.id == "action_2"
    next_actions_arg_action2 = action2_call_args[0][1]
    assert next_actions_arg_action2 == []
    prev_actions_arg_action2 = action2_call_args[0][2]
    assert len(prev_actions_arg_action2) == 1
    prev_action, score = prev_actions_arg_action2[0]
    assert prev_action.id == "action_1"
    assert score == 1.0

    # check the add_tool method was not called
    mock_add_tool_method.assert_not_called()


def test_chain_with_tuple(mocker):
    """Test the chain method with tuple of actions and tools."""
    wrapper = ToolkitWrapper()

    mock_add_action_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_action",
        new_callable=mock.Mock,
    )
    mock_add_tool_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_tool",
        new_callable=mock.Mock,
    )

    tool1 = ExampleQuery()
    tool1._id = "tool_1"
    action1 = Action(
        id="action_1",
        name="action_1",
        description="action_description_1",
        tools=[],
    )
    tool2 = ExampleQuery()
    tool2._id = "tool_2"

    # call the chain method with tuple containing action and tools
    wrapper.chain((action1, tool1), tool2)

    # check the add_action method was called once
    mock_add_action_method.assert_called_once_with(action1, [], [])

    # check the add_tool method was called twice
    assert mock_add_tool_method.call_count == 2

    # check first tool is connected to action1
    tool1_call_args = mock_add_tool_method.call_args_list[0]
    tool1_arg_add_tool = tool1_call_args[0][0]
    assert tool1_arg_add_tool.id == "tool_1"
    connected_actions_arg_tool1 = tool1_call_args[1]["connected_actions"]
    assert len(connected_actions_arg_tool1) == 1
    connected_action, score = connected_actions_arg_tool1[0]
    assert connected_action.id == "action_1"
    assert score == 1.0

    # check second tool has no connected actions (no preceding action)
    tool2_call_args = mock_add_tool_method.call_args_list[1]
    tool2_arg_add_tool = tool2_call_args[0][0]
    assert tool2_arg_add_tool.id == "tool_2"
    connected_actions_arg_tool2 = tool2_call_args[1]["connected_actions"]
    assert connected_actions_arg_tool2 == []
