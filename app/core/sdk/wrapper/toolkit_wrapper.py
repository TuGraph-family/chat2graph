from typing import Optional, Tuple, Union

from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit


class ToolkitWrapper:
    """Facade of the toolkit."""

    def __init__(self, toolkit: Optional[Toolkit] = None):
        self._toolkit: Toolkit = toolkit or Toolkit()

    @property
    def toolkit(self) -> Toolkit:
        """Get the toolkit."""
        return self._toolkit

    def chain(
        self,
        *item_chain: Union[Action, Tool, Tuple[Union[Action, Tool], ...]],
    ) -> "ToolkitWrapper":
        """Chain actions and tools together in the toolkit graph.

        Items are connected sequentially: Action -> Action, Action -> Tool.
        If a tuple of items is provided, they will be chained sequentially within the tuple.

        Args:
            item_chain: Actions, Tools, or tuples of actions/tools to chain

        Examples:
            # Chain actions and tools
            wrapper.chain(action1, tool1, action2, tool2)

            # Chain with tuples for grouped sequences
            wrapper.chain(
                action1,
                (action2, tool1),  # Sequential chain within tuple
                action3,
                tool2
            )
        """
        toolkit_service: ToolkitService = ToolkitService.instance

        # Flatten the chain to handle both individual items and tuples
        flattened_chain = []
        for item in item_chain:
            if isinstance(item, tuple):
                flattened_chain.extend(item)
            else:
                flattened_chain.append(item)

        # Process each item and create connections
        for i, item in enumerate(flattened_chain):
            if isinstance(item, Action):
                # Add action to the graph
                next_actions = []
                prev_actions = []

                # Connect to next item if it's an Action
                if i + 1 < len(flattened_chain) and isinstance(flattened_chain[i + 1], Action):
                    next_actions.append((flattened_chain[i + 1], 1.0))

                # Connect from previous item if it's an Action
                if i > 0 and isinstance(flattened_chain[i - 1], Action):
                    prev_actions.append((flattened_chain[i - 1], 1.0))

                toolkit_service.add_action(item, next_actions, prev_actions)

            elif isinstance(item, Tool):
                # Connect tool to previous action if exists
                connected_actions = []
                if i > 0 and isinstance(flattened_chain[i - 1], Action):
                    connected_actions.append((flattened_chain[i - 1], 1.0))

                toolkit_service.add_tool(item, connected_actions=connected_actions)
            else:
                raise ValueError(f"Invalid chain item: {item}. Must be Action or Tool.")

        return self
