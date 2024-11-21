from typing import List, Set

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D

from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool


class ToolkitGraphType:
    """The toolkit graph type."""

    ACTION = "action"
    TOOL = "tool"
    ACTION_CALL_TOOL = "call"
    ACTION_NEXT_ACTION = "next"


class Toolkit:
    """The toolkit is a collection of actions and tools.

    In the toolkit graph, the actions are connected to the tools.
        Action --Next--> Action
        Action --Call--> Tool

    Action node schema:
        {
            "type": "action",
            "data": Action
        }
    Tool node schema:
        {
            "type": "tool",
            "data": Tool
        }
    Action-Tool edge schema:
        {
            "type": "call",
            "score": float
        }
    Action-Action edge schema:
        {
            "type": "next",
            "score": float
        }

    Attributes:
        toolkit_graph (nx.DiGraph): The toolkit graph.
    """

    def __init__(self):
        # graph db
        self.toolkit_graph: nx.DiGraph = nx.DiGraph()

    def add_tool(self, tool: Tool, connected_actions: List[tuple[Action, float]]):
        """Add tool to toolkit graph. Action --Call--> Tool.

        Args:
            tool: The tool to be added
            connected_actions: List of tuples (action, score) that call this tool
        """
        has_connected_actions = False
        # add tool node if not exists
        if tool.id not in self.toolkit_graph:
            self.toolkit_graph.add_node(tool.id, type=ToolkitGraphType.TOOL, data=tool)

        # add edges from actions to tool
        for action, score in connected_actions:
            if action.id in self.toolkit_graph:
                self.toolkit_graph.add_edge(
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
            self.toolkit_graph.remove_node(tool.id)

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
        if action.id not in self.toolkit_graph:
            self.toolkit_graph.add_node(
                action.id, type=ToolkitGraphType.ACTION, data=action
            )

        # add edges to next actions
        for next_action, score in next_actions:
            if next_action.id in self.toolkit_graph:
                self.toolkit_graph.add_edge(
                    action.id,
                    next_action.id,
                    type=ToolkitGraphType.ACTION_NEXT_ACTION,
                    score=score,
                )

        # add edges from previous actions
        for prev_action, score in prev_actions:
            if prev_action.id in self.toolkit_graph:
                self.toolkit_graph.add_edge(
                    prev_action.id,
                    action.id,
                    type=ToolkitGraphType.ACTION_NEXT_ACTION,
                    score=score,
                )

    def remove_tool(self, tool_id: str):
        """Remove tool from the toolkit graph.

        Args:
            tool_id: ID of the tool to remove
        """
        if tool_id in self.toolkit_graph:
            self.toolkit_graph.remove_node(tool_id)

    def remove_action(self, action_id: str):
        """Remove action from the toolkit graph.

        Args:
            action_id: ID of the action to remove
        """
        if action_id not in self.toolkit_graph:
            return

        # clean up the dirty tool nodes
        out_edges = self.toolkit_graph[action_id]
        for neighbor_id, edge_data in out_edges.items():
            # if the called tool is only called by this action, remove the tool
            if (
                edge_data["type"] == ToolkitGraphType.ACTION_CALL_TOOL
                and self.toolkit_graph.in_degree(neighbor_id) == 1
            ):
                self.toolkit_graph.remove_node(neighbor_id)

        # remove the action
        if action_id in self.toolkit_graph:
            self.toolkit_graph.remove_node(action_id)

    async def recommend_toolkit_subgraph(
        self, actions: List[Action], threshold: float = 0.5, hops: int = 0
    ) -> nx.DiGraph:
        """Returns a subgraph containing recommended actions and their tools.

        Args:
            actions: The input actions to search for recommendations
            threshold: Minimum edge score to consider
            hops: Number of steps to search in the graph

        Returns:
            nx.DiGraph: Subgraph containing relevant actions and tools
        """
        # get initial action node ids
        node_ids_to_keep: Set[str] = {
            action.id for action in actions if action.id in self.toolkit_graph
        }

        # do BFS to get all action node ids within hops
        current_node_ids = node_ids_to_keep.copy()
        for _ in range(hops):
            next_node_ids = set()
            for node_id in current_node_ids:
                # find next actions connected with score >= threshold
                for neighbor_id in self.toolkit_graph.successors(node_id):
                    edge_data = self.toolkit_graph.get_edge_data(node_id, neighbor_id)
                    if (
                        edge_data["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
                        and edge_data["score"] >= threshold
                    ):
                        next_node_ids.add(neighbor_id)
                        node_ids_to_keep.add(neighbor_id)

            current_node_ids = next_node_ids
            if not current_node_ids:
                break

        # for all found actions, add their connected tools
        action_node_ids = {
            n for n in node_ids_to_keep
        }  # copy to avoid modification during iteration
        for action_node_id in action_node_ids:
            for tool_id in self.toolkit_graph.successors(action_node_id):
                edge_data = self.toolkit_graph.get_edge_data(action_node_id, tool_id)
                # add tools that are called with score >= threshold
                if (
                    edge_data["type"] == ToolkitGraphType.ACTION_CALL_TOOL
                    and edge_data["score"] >= threshold
                ):
                    node_ids_to_keep.add(tool_id)

        original_toolkit_subgraph: nx.DiGraph = self.toolkit_graph.subgraph(
            node_ids_to_keep
        )
        toolkit_subgraph = original_toolkit_subgraph.copy()

        # remove edges that don't meet the threshold
        edges_to_remove = [
            (u, v)
            for u, v, d in toolkit_subgraph.edges(data=True)
            if d["score"] < threshold
        ]
        toolkit_subgraph.remove_edges_from(edges_to_remove)
        self.visualize_toolkit_graph(
            graph=toolkit_subgraph, title="Recommended Toolkit"
        )
        plt.show(block=True)

        return toolkit_subgraph

    async def update_toolkit_graph(self, text: str, called_tools: List[Tool]):
        """Update the toolkit graph by reinforcement learning.

        Args:
            text: Input text describing the context
            called_tools: List of tools that were called in this interaction
        """
        # TODO: simple reinforcement learning implementation
        # Increase weight of edges leading to successful tool calls

    def visualize_toolkit_graph(self, graph: nx.DiGraph, title: str):
        """Visualize the toolkit graph with different colors for actions and tools.

        Args:
            graph: The graph to visualize
            title: Title for the plot
        """
        plt.figure(figsize=(12, 8))

        # Get node positions using spring layout with larger distance and more iterations
        pos = nx.spring_layout(
            graph, k=2, iterations=200
        )  # increase k and iterations for better layout

        # Draw nodes
        action_nodes = [
            n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.ACTION
        ]
        tool_nodes = [
            n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.TOOL
        ]

        # Draw action nodes in blue
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=action_nodes,
            node_color="lightblue",
            node_size=2000,
            node_shape="o",
        )

        # Draw tool nodes in green
        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=tool_nodes,
            node_color="lightgreen",
            node_size=1500,
            node_shape="s",
        )

        # Draw edges with different colors and styles for different types
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

        # Draw action-to-action edges in blue with curved arrows
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=next_edges,
            edge_color="blue",
            arrows=True,
            arrowsize=35,
            width=2,
        )

        # Draw action-to-tool edges in green with different curve style
        nx.draw_networkx_edges(
            graph,
            pos,
            edgelist=call_edges,
            edge_color="green",
            arrows=True,
            arrowsize=35,
            width=1.5,
        )

        # Add edge labels (scores) with adjusted positions for curved edges
        edge_labels = {
            (u, v): f"{d['score']:.2f}" for (u, v, d) in graph.edges(data=True)
        }
        nx.draw_networkx_edge_labels(
            graph,
            pos,
            edge_labels,
            font_size=8,
            label_pos=0.5,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
        )

        # Add node labels - handle both Action and Tool nodes
        node_labels = {}
        for n, d in graph.nodes(data=True):
            if d["type"] == ToolkitGraphType.ACTION:
                node_labels[n] = d["data"].id
            elif d["type"] == ToolkitGraphType.TOOL:
                node_labels[n] = d["data"].id

        # Draw labels with white background for better visibility
        nx.draw_networkx_labels(
            graph,
            pos,
            node_labels,
            font_size=8,
            # bbox=dict(facecolor="white", edgecolor="none", alpha=0.7),
        )

        plt.title(title)
        plt.axis("off")

        # Add a legend

        legend_elements = [
            Line2D([0], [0], color="blue", label="Action→Action"),
            Line2D([0], [0], color="green", label="Action→Tool"),
            plt.scatter([0], [0], color="lightblue", s=100, label="Action"),
            plt.scatter([0], [0], color="lightgreen", marker="s", s=100, label="Tool"),
        ]
        plt.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(1, 1))

        plt.tight_layout()
        return plt.gcf()
