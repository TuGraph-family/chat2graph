from unittest import mock

from app.core.sdk.wrapper.toolkit_wrapper import ToolkitWrapper
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from test.resource.tool_resource import Query

ToolkitService()


def test_action(mocker):
    """Test the action method."""
    wrapper = ToolkitWrapper()
    mock_add_action_method = mocker.patch(
        "app.core.sdk.wrapper.toolkit_wrapper.ToolkitService.add_action",
        new_callable=mock.Mock,
    )

    action = Action(id="test_action_id", name="test_action", description="test_description")
    tools = [Query(id="test_query_id")]

    # call the action method
    wrapper.action(action, tools)

    # check add_action was called, and the parameters are correct
    mock_add_action_method.assert_called_once_with(action, [], [])


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

    tool = Query(id="test_tool_id")
    action = Action(
        id="test_action_id",
        name="action",
        description="test_description",
        tools=[tool],
    )

    # call the chain method with a single action
    wrapper.chain(action)

    # check the add_action method was called once
    mock_add_action_method.assert_called_once_with(action, [], [])

    # check the add_action method was called with by single action
    mock_add_tool_method.assert_called_once_with(tool, connected_actions=[(action, 1.0)])


def test_chain_multiple_actions(mocker):
    """Test the chain method with multiple actions in a tuple."""
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
        tools=[Query(id="tool_1")],
    )
    action2 = Action(
        id="action_2",
        name="action_2",
        description="action_description_2",
        tools=[Query(id="tool_2")],
    )

    # call the chain method with a tuple of 2 actions
    wrapper.chain((action1, action2))

    # check the add_action method was called twice (once for each action)
    assert mock_add_action_method.call_count == 2

    # check the add_action method was called with action1 (first call)
    action1_call_args = mock_add_action_method.call_args_list[0]
    action1_arg_add_action = action1_call_args[0][0]
    assert action1_arg_add_action.id == "action_1"
    assert action1_arg_add_action.tools == []
    next_actions_arg_action1 = action1_call_args[1]["next_actions"]
    assert len(next_actions_arg_action1) == 1
    next_action, score = next_actions_arg_action1[0]
    assert next_action.id == "action_2"
    assert score == 1.0
    prev_actions_arg_action1 = action1_call_args[1]["prev_actions"]
    assert prev_actions_arg_action1 == []

    # check the add_action method was called with action2 (second call)
    action2_call_args = mock_add_action_method.call_args_list[1]
    action2_arg_add_action = action2_call_args[0][0]
    assert action2_arg_add_action.id == "action_2"
    assert action2_arg_add_action.tools == []
    next_actions_arg_action2 = action2_call_args[1]["next_actions"]
    assert next_actions_arg_action2 == []
    prev_actions_arg_action2 = action2_call_args[1]["prev_actions"]
    assert len(prev_actions_arg_action2) == 1
    prev_action, score = prev_actions_arg_action2[0]
    assert prev_action.id == "action_1"
    assert score == 1.0

    # check the add_tool method was called twice (once for each tool)
    assert mock_add_tool_method.call_count == 2

    # check the add_tool method was called with tool_1 (first call)
    tool1_call_args = mock_add_tool_method.call_args_list[0]
    tool1_arg_add_tool = tool1_call_args[0][0]
    assert tool1_arg_add_tool.id == "tool_1"
    connected_actions_arg_tool1 = tool1_call_args[1]["connected_actions"]
    assert len(connected_actions_arg_tool1) == 1
    connected_action, score = connected_actions_arg_tool1[0]
    assert connected_action.id == "action_1"
    assert score == 1.0

    # check the add_tool method was called with tool_2 (second call)
    tool2_call_args = mock_add_tool_method.call_args_list[1]
    tool2_arg_add_tool = tool2_call_args[0][0]
    assert tool2_arg_add_tool.id == "tool_2"
    connected_actions_arg_tool2 = tool2_call_args[1]["connected_actions"]
    assert len(connected_actions_arg_tool2) == 1
    connected_action, score = connected_actions_arg_tool2[0]
    assert connected_action.id == "action_2"
    assert score == 1.0
