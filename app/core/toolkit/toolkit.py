from typing import List, Optional, Set, Tuple

from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import networkx as nx  # type: ignore

from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool


class ToolkitGraphType:
    """The toolkit graph type."""

    ACTION = "action"
    TOOL = "tool"
    ACTION_CALL_TOOL = "call"
    ACTION_NEXT_ACTION = "next"


class Toolkit:
    """The toolkit is a collection of actions and tools.

    In the toolkit graph, the actions are connected to the tools:
        Action --Next--> Action
        Action --Call--> Tool


    Node schema:
        {
            "node_id": {
                "type": "action" | "tool",
                "data": Action | Tool
            }
        }
    Edge schema:
        {
            "edge_id": {
                "type": "call" | "next",
                "score": float
            }
        }

    Attributes:
        toolkit_graph (nx.DiGraph): The toolkit graph.
    """

    def __init__(self):
        self._toolkit_graph: nx.DiGraph = nx.DiGraph()

    def verify_actions(self, actions: List[Action]) -> bool:
        """Verify if all action ids are in the toolkit graph.

        Args:
            actions: List of actions to verify

        Returns:
            bool: True if all action ids are in the toolkit graph
        """
        verified = True
        for action in actions:
            if action.id not in self._toolkit_graph:
                verified = False
                break
        return verified

    def add_tool(self, tool: Tool, connected_actions: List[tuple[Action, float]]):
        """Add tool to toolkit graph. Action --Call--> Tool.

        Args:
            tool: The tool to be added
            connected_actions: List of tuples (action, score) that call this tool
        """
        has_connected_actions = False
        # add tool node if not exists
        if tool.id not in self._toolkit_graph:
            self._toolkit_graph.add_node(tool.id, type=ToolkitGraphType.TOOL, data=tool)

        # add edges from actions to tool
        for action, score in connected_actions:
            if action.id in self._toolkit_graph:
                self._toolkit_graph.add_edge(
                    action.id,
                    tool.id,
                    type=ToolkitGraphType.ACTION_CALL_TOOL,
                    score=score,
                )
                has_connected_actions = True
            else:
                print(f"warning: Action {action.id} not in the toolkit graph")

        if not has_connected_actions:
            print(f"warning: Tool {tool.id} has no connected actions")
            self._toolkit_graph.remove_node(tool.id)

    def add_action(
        self,
        action: Action,
        next_actions: List[tuple[Action, float]],
        prev_actions: List[tuple[Action, float]],
    ):
        """Add action to the toolkit graph. Action --Next--> Action.

        Args:
            action: The action to be added
            next_actions: List of tuples (action, score) that follow this action
            prev_actions: List of tuples (action, score) that precede this action
        """
        # add action node if not exists
        if action.id not in self._toolkit_graph:
            self._toolkit_graph.add_node(action.id, type=ToolkitGraphType.ACTION, data=action)

        # add edges to next actions
        for next_action, score in next_actions:
            if next_action.id in self._toolkit_graph:
                self._toolkit_graph.add_edge(
                    action.id,
                    next_action.id,
                    type=ToolkitGraphType.ACTION_NEXT_ACTION,
                    score=score,
                )

        # add edges from previous actions
        for prev_action, score in prev_actions:
            if prev_action.id in self._toolkit_graph:
                self._toolkit_graph.add_edge(
                    prev_action.id,
                    action.id,
                    type=ToolkitGraphType.ACTION_NEXT_ACTION,
                    score=score,
                )

    def get_action(self, action_id: str) -> Action:
        """Get action from the toolkit graph.

        Args:
            action_id: ID of the action to get

        Returns:
            Action: The action with the given ID
        """
        if action_id in self._toolkit_graph:
            return self._toolkit_graph.nodes[action_id]["data"]
        raise ValueError(f"Action {action_id} not found in the toolkit graph")

    def remove_tool(self, tool_id: str):
        """Remove tool from the toolkit graph.

        Args:
            tool_id: ID of the tool to remove
        """
        if tool_id in self._toolkit_graph:
            self._toolkit_graph.remove_node(tool_id)

    def remove_action(self, action_id: str):
        """Remove action from the toolkit graph.

        Args:
            action_id: ID of the action to remove
        """
        if action_id not in self._toolkit_graph:
            return

        # clean up the dirty tool nodes
        out_edges = self._toolkit_graph[action_id]
        for neighbor_id, edge_data in out_edges.items():
            # if the called tool is only called by this action, remove the tool
            if (
                edge_data["type"] == ToolkitGraphType.ACTION_CALL_TOOL
                and self._toolkit_graph.in_degree(neighbor_id) == 1
            ):
                self._toolkit_graph.remove_node(neighbor_id)

        # remove the action
        if action_id in self._toolkit_graph:
            self._toolkit_graph.remove_node(action_id)

    async def recommend_subgraph(
        self, actions: List[Action], threshold: float = 0.5, hops: int = 0
    ) -> nx.DiGraph:
        """It is a recommendation engine that extracts a relevant subgraph from a
        toolkit graph based on input actions. It performs a weighted breadth-first
        search (BFS) to find related actions within specified hops, then associates
        relevant tools with these actions. The resulting subgraph contains both
        actions and their tools, filtered by a score threshold.

        The function works in three main steps:
        1. Initializes with input actions and expands to related actions using BFS
        within hop limit
        2. Adds relevant tools connected to the found actions
        3. Filters edges based on score threshold and returns the final subgraph

        Args:
            actions: The input actions to search for recommendations
            threshold: Minimum edge score to consider
            hops: Number of steps to search in the graph

        Returns:
            nx.DiGraph: Subgraph containing relevant actions and tools
        """
        # get initial action node ids
        node_ids_to_keep: Set[str] = {
            action.id for action in actions if action.id in self._toolkit_graph
        }

        # do BFS to get all action node ids within hops
        current_node_ids = node_ids_to_keep.copy()
        for _ in range(hops):
            next_node_ids: Set[str] = set()
            for node_id in current_node_ids:
                # find next actions connected with score >= threshold
                for neighbor_id in self._toolkit_graph.successors(node_id):
                    edge_data = self._toolkit_graph.get_edge_data(node_id, neighbor_id)
                    if (
                        edge_data["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
                        and edge_data["score"] >= threshold
                    ):
                        next_node_ids.add(neighbor_id)
                        node_ids_to_keep.add(neighbor_id)

            current_node_ids = next_node_ids
            if not current_node_ids:
                break

        # for all found actions, add their connected tools to the found actions
        action_node_ids: Set[str] = set(node_ids_to_keep)
        for action_node_id in action_node_ids:
            for tool_id in self._toolkit_graph.successors(action_node_id):
                edge_data = self._toolkit_graph.get_edge_data(action_node_id, tool_id)
                # add tools that are called with score >= threshold
                if (
                    edge_data["type"] == ToolkitGraphType.ACTION_CALL_TOOL
                    and edge_data["score"] >= threshold
                ):
                    node_ids_to_keep.add(tool_id)

        original_toolkit_subgraph: nx.DiGraph = self._toolkit_graph.subgraph(node_ids_to_keep)
        toolkit_subgraph = original_toolkit_subgraph.copy()

        # remove edges that don't meet the threshold
        edges_to_remove = [
            (u, v) for u, v, d in toolkit_subgraph.edges(data=True) if d["score"] < threshold
        ]
        toolkit_subgraph.remove_edges_from(edges_to_remove)
        self.visualize(graph=toolkit_subgraph, title="Recommended Toolkit")

        return toolkit_subgraph

    async def recommend_tools(
        self, actions: List[Action], threshold: float = 0.5, hops: int = 0
    ) -> Tuple[List[Tool], List[Action]]:
        """Recommend tools and actions.

        Args:
            actions: List of actions to recommend tools for
            threshold: Minimum score threshold for recommendations
            hops: Number of hops to search for recommendations

        Returns:
            nx.DiGraph: The toolkit subgraph with recommended tools
        """
        subgraph = await self.recommend_subgraph(actions, threshold, hops)
        actions = [
            subgraph.nodes[n]["data"]
            for n, d in subgraph.nodes(data=True)
            if d["type"] == ToolkitGraphType.ACTION
        ]
        tools = [
            subgraph.nodes[n]["data"]
            for n, d in subgraph.nodes(data=True)
            if d["type"] == ToolkitGraphType.TOOL
        ]
        return tools, actions

    async def update_action(self, text: str, called_tools: List[Tool]):
        """Update the toolkit graph by reinforcement learning.

        Args:
            text: Input text describing the context
            called_tools: List of tools that were called in this interaction
        """
        # TODO: simple reinforcement learning implementation
        # Increase weight of edges leading to successful tool calls

    def visualize(self, graph: nx.DiGraph, title: str, show=True):
        """Visualize the toolkit graph with different colors for actions and tools.

        Args:
            graph: The graph to visualize.
            title: Title for the plot.
            show: Whether to show the plot.

        Returns:
            plt.Figure: The plot figure.
        """
        plt.figure(figsize=(12, 8))

        # get node positions using spring layout with larger distance and more iterations
        pos = nx.spring_layout(
            graph, k=2, iterations=200
        )  # increase k and iterations for better layout

        # draw nodes
        action_nodes = [
            n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.ACTION
        ]
        tool_nodes = [n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.TOOL]

        # draw action nodes in blue
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=action_nodes,
            node_color="lightblue",
            node_size=2000,
            node_shape="o",
        )

        # draw tool nodes in green
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=tool_nodes,
            node_color="lightgreen",
            node_size=1500,
            node_shape="s",
        )

        # draw edges with different colors and styles for different types
        next_edges = [
            (u, v)
            for (u, v, d) in graph.edges(data=True)
            if d["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
        ]
        call_edges = [
            (u, v)
            for (u, v, d) in graph.edges(data=True)
            if d["type"] == ToolkitGraphType.ACTION_CALL_TOOL
        ]

        # draw action-to-action edges in blue with curved arrows
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=next_edges,
            edge_color="blue",
            arrows=True,
            arrowsize=35,
            width=2,
        )

        # draw action-to-tool edges in green with different curve style
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=call_edges,
            edge_color="green",
            arrows=True,
            arrowsize=35,
            width=1.5,
        )

        # add edge labels (scores) with adjusted positions for curved edges
        edge_labels = {(u, v): f"{d['score']:.2f}" for (u, v, d) in graph.edges(data=True)}
        nx.draw_networkx_edge_labels(
            graph,
            pos,
            edge_labels,
            font_size=8,
            label_pos=0.5,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7},
        )

        # add node labels - handle both Action and Tool nodes
        node_labels = {}
        for n, d in graph.nodes(data=True):
            if d["type"] == ToolkitGraphType.ACTION:
                node_labels[n] = d["data"].id
            elif d["type"] == ToolkitGraphType.TOOL:
                node_labels[n] = d["data"].id

        # draw labels with white background for better visibility
        nx.draw_networkx_labels(
            graph,
            pos,
            node_labels,
            font_size=8,
            # bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
        )

        plt.title(title)
        plt.axis("off")

        # add a legend

        legend_elements = [
            Line2D([0], [0], color="blue", label="Action→Action"),
            Line2D([0], [0], color="green", label="Action→Tool"),
            plt.scatter([0], [0], color="lightblue", s=100, label="Action"),
            plt.scatter([0], [0], color="lightgreen", marker="s", s=100, label="Tool"),
        ]
        plt.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1, 1))

        plt.tight_layout()

        if show:
            plt.show(block=False)
        return plt.gcf()


class ToolkitService:
    """The toolkit service provides functionalities for the toolkit."""

    def __init__(self, toolkit: Optional[Toolkit] = None):
        # it manages one toolkit for now, but can be extended to manage multiple toolkits
        if not toolkit:
            toolkit = Toolkit()
        self._toolkit = toolkit

    def create_toolkit(self) -> Toolkit:
        """Create a new toolkit."""
        return Toolkit()

    def update_toolkit(self, toolkit: Toolkit) -> None:
        """Update the toolkit."""
        self._toolkit = toolkit

    def remove_toolkit(self, args: dict) -> None:
        """Remove a toolkit."""
        # since there is only one toolkit, it is not removed for now

    def get_toolkit(self) -> Toolkit:
        """Get the current toolkit."""
        return self._toolkit
