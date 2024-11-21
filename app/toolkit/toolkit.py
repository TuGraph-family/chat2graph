from typing import List

from dbgpt.storage.graph_store.graph import MemoryGraph

from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool


class Toolkit:
    """Toolkit is a collection of actions and tools.

    In the toolkit graph, the actions are connected to the tools.
        Action --Next--> Action
        Action --Call--> Tool
    """

    def __init__(self):
        self._id = None
        self._actions: List[Action] = None
        self._tools: List[Tool] = None

        # graph db
        self._toolkit_graph: MemoryGraph = None

    def add_tool(self):
        """Add tool to toolkit graph. Action --Call--> Tool."""

    def add_action(self):
        """Add action to the toolkit graph. Action --Next--> Action."""

    def remove_tool(self):
        """Remove tool from the toolkit graph."""

    def remove_action(self):
        """Remove action from the toolkit graph."""

    async def recommend_actions_and_tools(self) -> List[Action]:
        """Recommend actions and tools from the toolkit graph."""

    async def update_toolkit_graph(self, text: str, called_tools: List[Tool]):
        """Update the toolkit graph by renforcement learning."""
        # TODO: implement the reinforcement learning algorithm in S1

    def init_action_tool_graph(
        self, text: str, actions: List[Action], tools: List[Tool]
    ):
        """Initialize the action-tool graph."""
        # TODO: to simplify the problem, let the `text` be not used, and the `actions` and `tools` be used.
