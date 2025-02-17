from typing import List, Optional, Tuple, Union
from uuid import uuid4

from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit


class ToolkitWrapper:
    """Facade of the toolkit."""

    def __init__(self, id: Optional[str] = None):
        self._toolkit_id: str = id or str(uuid4())
        self._toolkit: Toolkit = Toolkit()

    @property
    def toolkit(self) -> Toolkit:
        """Get the toolkit."""
        return self._toolkit

    def action(self, action: Action, tools: Optional[List[Tool]] = None) -> "ToolkitWrapper":
        """Syntactic Sugar of add_action."""
        action.tools = tools or []
        toolkit_service: ToolkitService = ToolkitService.instance or ToolkitService()
        toolkit_service.add_action(self._toolkit_id, action, [], [])
        action.tools = []  # clear tools from the action
        return self

    def chain(self, *action_chain: Union[Action, Tuple[Action, ...]]) -> "ToolkitWrapper":
        """Chain actions together in the toolkit graph.

        If a tuple of actions is provided, they will be chained sequentially.
        """
        for item in action_chain:
            toolkit_service: ToolkitService = ToolkitService.instance or ToolkitService()

            if isinstance(item, Action):
                # add action to the graph
                toolkit_service.add_action(self._toolkit_id, item, [], [])
                # connect tools to the action
                for tool in item.tools:
                    # TODO: configure the default score for the action-call->tool edge
                    toolkit_service.add_tool(
                        self._toolkit_id, tool, connected_actions=[(item, 1.0)]
                    )

                # clear tools from the action
                item.tools = []
            elif isinstance(item, tuple) and all(isinstance(a, Action) for a in item):
                # process chain of actions in the tuple
                for i in range(len(item) - 1):
                    from_action, to_action = item[i], item[i + 1]
                    # connect two consecutive actions
                    # TODO: configure the default score for the action-next->action edge
                    toolkit_service.add_action(
                        self._toolkit_id,
                        from_action,
                        next_actions=[(to_action, 1.0)],
                        prev_actions=[],
                    )
                    toolkit_service.add_action(
                        self._toolkit_id,
                        to_action,
                        next_actions=[],
                        prev_actions=[(from_action, 1.0)],
                    )

                for action in item:
                    for tool in action.tools:
                        # connect tools to the actions
                        # TODO: configure the default score for the action-call->tool edge
                        toolkit_service.add_tool(
                            self._toolkit_id, tool, connected_actions=[(action, 1.0)]
                        )
                        # clear tools from all actions in the tuple
                        action.tools = []
            else:
                raise ValueError(f"Invalid chain item: {item}.")

        return self
