from typing import Any, List, Optional, Tuple, Union

from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit, ToolkitService


class ToolkitWrapper:
    """Facade of the toolkit."""

    def __init__(self):
        self._toolkit_service: ToolkitService = ToolkitService()

    def action(self, action: Action, tools: Optional[List[Tool]] = None) -> None:
        """Syntactic Sugar of add_action."""
        action.tools = tools or []
        self._toolkit_service.add_action(action, [], [])
        action.tools = []  # clear tools from the action

    def chain(self, *action_chain: Union[Action, Tuple[Action, ...]]) -> Toolkit:
        """Chain actions together in the toolkit graph.

        If a tuple of actions is provided, they will be chained sequentially.
        """
        for item in action_chain:
            if isinstance(item, Action):
                # add action to the graph
                self._toolkit_service.add_action(item, [], [])
                # connect tools to the action
                for tool in item.tools:
                    # TODO: configure the default score for the action-call->tool edge
                    self._toolkit_service.add_tool(tool, connected_actions=[(item, 1.0)])

                # clear tools from the action
                item.tools = []
            elif isinstance(item, tuple) and all(isinstance(a, Action) for a in item):
                # process chain of actions in the tuple
                for i in range(len(item) - 1):
                    from_action, to_action = item[i], item[i + 1]
                    # connect two consecutive actions
                    # TODO: configure the default score for the action-next->action edge
                    self._toolkit_service.add_action(
                        from_action, next_actions=[(to_action, 1.0)], prev_actions=[]
                    )
                    self._toolkit_service.add_action(
                        to_action, next_actions=[], prev_actions=[(from_action, 1.0)]
                    )

                for action in item:
                    for tool in action.tools:
                        # connect tools to the actions
                        # TODO: configure the default score for the action-call->tool edge
                        self._toolkit_service.add_tool(tool, connected_actions=[(action, 1.0)])
                        # clear tools from all actions in the tuple
                        action.tools = []
            else:
                raise ValueError(f"Invalid chain item: {item}.")

        return self._toolkit_service.get_toolkit()

    def update_action(self, action: Action, arg: Any) -> None:
        """Update the action in the toolkit graph."""
        # TODO: implement the add_operator method
        raise NotImplementedError("This method is not implemented")

    def train(self, *args: Any, **kwargs: Any) -> Any:
        """Train the toolkit by RL."""
        # TODO: implement the train method
        raise NotImplementedError("This method is not implemented")
