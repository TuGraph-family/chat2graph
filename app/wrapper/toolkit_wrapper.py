from typing import List, Optional, Union

from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool
from app.toolkit.toolkit import Toolkit


class ToolkitWrapper:
    """Wrapper for interacting with the toolkit."""

    def __init__(self):
        self._toolkit: Toolkit = Toolkit()

    def action(self, action: Action, tools: Optional[List[Tool]] = None) -> None:
        """Syntactic Sugar of add_action."""
        action.tools = tools or []
        self._toolkit.add_action(action, [], [])

    def chain(self, *action_chain: Union[Action, tuple[Action, Action]]) -> None:
        """Chain actions together in the toolkit graph."""
        for item in action_chain:
            if isinstance(item, Action):
                # add action to the graph
                self._toolkit.add_action(item, [], [])
                # connect tools to the action
                for tool in item.tools:
                    # TODO: configure the default score for the action-call->tool edge
                    self._toolkit.add_tool(tool, connected_actions=[(item, 1.0)])

                # clear tools from the action
                item.tools = []
            elif (
                isinstance(item, tuple)
                and len(item) == 2
                and isinstance(item[0], Action)
                and isinstance(item[1], Action)
            ):
                from_action, to_action = item
                # connect two actions
                # TODO: configure the default score for the action-next->action edge
                self._toolkit.add_action(
                    from_action, next_actions=[(to_action, 1.0)], prev_actions=[]
                )
                self._toolkit.add_action(
                    to_action, next_actions=[], prev_actions=[(from_action, 1.0)]
                )

                # connect tools to the actions
                # TODO: configure the default score for the action-call->tool edge
                for tool in from_action.tools:
                    self._toolkit.add_tool(tool, connected_actions=[(from_action, 1.0)])
                for tool in to_action.tools:
                    self._toolkit.add_tool(tool, connected_actions=[(to_action, 1.0)])

                # clear tools from actions
                from_action.tools = []
                to_action.tools = []
            else:
                raise ValueError(f"Invalid chain item: {item}.")
