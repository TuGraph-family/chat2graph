from typing import Any, List, Optional, Tuple, Union

from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_group import ToolGroup
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
        *item_chain: Union[Action, Tool, ToolGroup, Tuple[Union[Action, Tool, ToolGroup], ...]],
    ) -> "ToolkitWrapper":
        """Chain actions, tools, and tool groups together in the toolkit graph.

        Valid connection patterns:
        - Action -> Action
        - Action -> Tool
        - Action -> ToolGroup
        - Action -> (Tool, Tool, ...) - connects Action to multiple Tools
        - Action -> (ToolGroup, ToolGroup, ...) - connects Action to multiple ToolGroups
        - Action -> (Tool, ToolGroup, ...) - connects Action to mixed Tools and ToolGroups
        - (Action, Tool, ToolGroup, ...) - sequential chain within tuple

        Invalid patterns (will raise ValueError):
        - Tool/ToolGroup as first item
        - Tool/ToolGroup followed by anything other than Action
        - A parallel tuple followed by anything other than an Action

        Args:
            item_chain (Union[Action, Tool, ToolGroup, Tuple[Union[Action, Tool, ToolGroup], ...]]):
                A sequence of Actions, Tools, ToolGroups, or tuples of Tools/ToolGroups to be
                chained.

        Examples:
            # Basic chains
            wrapper.chain(action1, tool1)
            wrapper.chain(action1, action2, tool1)

            # Action connecting to multiple tools
            wrapper.chain(action1, (tool1, tool2, tool3))

            # Action connecting to multiple tool groups
            wrapper.chain(action1, (tool_group1, tool_group2))

            # Mixed connections
            wrapper.chain(action1, (tool1, tool_group1), action2, tool2)

            # Sequential chain within tuple
            wrapper.chain((action1, tool1, tool_group1), action2)

            # Complex chain
            wrapper.chain(
                action1,
                (tool1, tool2),      # action1 connects to both tools
                action2,             # continues the chain
                tool_group1          # action2 connects to tool_group1
            )
        """
        toolkit_service: ToolkitService = ToolkitService.instance

        if not item_chain:
            return self

        # 1. Flatten sequential tuples
        processed_chain: List[Any] = []
        for item in item_chain:
            if isinstance(item, tuple) and item and isinstance(item[0], Action):
                processed_chain.extend(item)
            else:
                processed_chain.append(item)

        if not processed_chain:
            return self

        # 2. Validate and Process the chain in a single pass
        # The last action that can be a source for a connection
        last_action_source = None

        for i, current_item in enumerate(processed_chain):
            prev_item = processed_chain[i - 1] if i > 0 else None

            # --- Validation for the current item ---
            if i == 0 and not isinstance(current_item, Action):
                raise ValueError("Chain must start with an Action.")

            if isinstance(prev_item, Tool | ToolGroup) and not isinstance(current_item, Action):
                raise ValueError(f"{type(prev_item).__name__} can only be followed by an Action.")

            if isinstance(prev_item, tuple) and not isinstance(current_item, Action):
                raise ValueError("A parallel connection tuple can only be followed by an Action.")

            # --- Processing and Connection ---
            if isinstance(current_item, Action):
                prev_actions: List[Tuple[Action, float]] = []
                # An action connects to the last action source
                if last_action_source:
                    prev_actions.append((last_action_source, 1.0))

                toolkit_service.add_action(current_item, prev_actions=prev_actions, next_actions=[])
                # This action is now the new source for subsequent tools/actions
                last_action_source = current_item

            elif isinstance(current_item, Tool | ToolGroup):
                if not isinstance(prev_item, Action):
                    # This case should be caught by validation, but as a safeguard:
                    raise ValueError(
                        f"{type(current_item).__name__} must be preceded by an Action."
                    )

                connected_actions = [(prev_item, 1.0)]
                if isinstance(current_item, Tool):
                    toolkit_service.add_tool(current_item, connected_actions=connected_actions)
                else:  # ToolGroup
                    toolkit_service.add_tool_group(
                        current_item, connected_actions=connected_actions
                    )

            elif isinstance(current_item, tuple):
                if not isinstance(prev_item, Action):
                    raise ValueError("A parallel connection tuple must be preceded by an Action.")

                for sub_item in current_item:
                    if not isinstance(sub_item, Tool | ToolGroup):
                        raise ValueError(
                            "Parallel connection tuples can only contain Tools or ToolGroups."
                        )

                    connected_actions = [(prev_item, 1.0)]
                    if isinstance(sub_item, Tool):
                        toolkit_service.add_tool(sub_item, connected_actions=connected_actions)
                    else:  # ToolGroup
                        toolkit_service.add_tool_group(
                            sub_item, connected_actions=connected_actions
                        )
            else:
                raise TypeError(f"Invalid chain item type: {type(current_item).__name__}")

        return self