from typing import Any, Dict, List, Optional, Set, Tuple, Union

import matplotlib
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import networkx as nx  # type: ignore

from app.core.common.singleton import Singleton
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.toolkit import Toolkit

# use non-interactive backend for matplotlib, to avoid blocking
matplotlib.use("Agg")


class ToolkitService(metaclass=Singleton):
    """The toolkit service provides functionalities for the toolkit."""

    def __init__(self):
        self._toolkit: Toolkit = Toolkit()

    def get_toolkit(self) -> Toolkit:
        """Get the current toolkit."""
        return self._toolkit

    def with_store(self, store_type: Any) -> "ToolkitService":
        """Use the store for the toolkit."""
        # TODO: implement the persistent storage for the toolkit
        raise NotImplementedError("This method is not implemented")

    def add_tool(self, tool: Tool, connected_actions: List[Tuple[Action, float]]):
        """Add tool to toolkit graph. Action --Call--> Tool.

        Args:
            tool (Tool): The tool to be added
            connected_actions (List[Tuple[Action, float]]): List of tuples (action, score) that
                call this tool
        """
        has_connected_actions = False
        # add tool vertex if not exists
        if tool.id not in self.get_toolkit().vertices():
            self.get_toolkit().add_vertex(tool.id, data=tool)

        # add edges from actions to tool
        for action, score in connected_actions:
            if action.id in self.get_toolkit().vertices():
                self.get_toolkit().add_edge(action.id, tool.id)
                self.get_toolkit().set_score(action.id, tool.id, score)
                has_connected_actions = True
            else:
                print(f"warning: Action {action.id} not in the toolkit graph")

        if not has_connected_actions:
            print(f"warning: Tool {tool.id} has no connected actions")
            self.get_toolkit().remove_vertex(tool.id)

    def add_action(
        self,
        action: Action,
        next_actions: List[Tuple[Action, float]],
        prev_actions: List[Tuple[Action, float]],
    ) -> None:
        """Add action to the toolkit graph. Action --Next--> Action.

        Args:
            action (Action): The action to be added
            next_actions (List[Tuple[Action, float]]): List of tuples (action, score) that follow
                this action
            prev_actions (List[Tuple[Action, float]]): List of tuples (action, score) that precede
                this action
        """
        # add action vertex if not exists
        if action.id not in self.get_toolkit().vertices():
            self.get_toolkit().add_vertex(action.id, data=action)

        # add edges to next actions
        for next_action, score in next_actions:
            if next_action.id in self.get_toolkit().vertices():
                self.get_toolkit().add_edge(action.id, next_action.id)
                self.get_toolkit().set_score(action.id, next_action.id, score)

        # add edges from previous actions
        for prev_action, score in prev_actions:
            if prev_action.id in self.get_toolkit().vertices():
                self.get_toolkit().add_edge(prev_action.id, action.id)
                self.get_toolkit().set_score(prev_action.id, action.id, score)

    def get_action(self, id: str, action_id: str) -> Action:
        """Get action from the toolkit graph."""
        action: Optional[Action] = self.get_toolkit().get_action(action_id)
        if not action:
            raise ValueError(f"Action {action_id} not found in the toolkit graph")
        return action

    def remove_tool(self, id: str, tool_id: str):
        """Remove tool from the toolkit graph."""
        self.get_toolkit().remove_vertex(tool_id)

    def remove_action(self, id: str, action_id: str):
        """Remove action from the toolkit graph."""
        self.get_toolkit().remove_vertex(action_id)

    def recommend_subgraph(
        self, actions: List[Action], threshold: float = 0.5, hops: int = 0
    ) -> Toolkit:
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
            actions (List[Action]): The input actions to search for recommendations
            threshold (float): Minimum edge score to consider
            hops (int): Number of steps to search in the graph

        Returns:
            nx.DiGraph: Subgraph containing relevant actions and tools
        """
        # get initial action vertex ids
        vertex_ids_to_keep: Set[str] = {
            action.id for action in actions if action.id in self.get_toolkit().vertices()
        }

        # do BFS to get all action vertex ids within hops
        current_vertex_ids = vertex_ids_to_keep.copy()
        for _ in range(hops):
            next_vertex_ids: Set[str] = set()
            for vertex_id in current_vertex_ids:
                # find next actions connected with score >= threshold
                for neighbor_id in self.get_toolkit().successors(vertex_id):
                    if (
                        self.get_toolkit().get_action(vertex_id)
                        and self.get_toolkit().get_action(neighbor_id)
                        and self.get_toolkit().get_score(vertex_id, neighbor_id) >= threshold
                    ):
                        next_vertex_ids.add(neighbor_id)
                        vertex_ids_to_keep.add(neighbor_id)

            current_vertex_ids = next_vertex_ids
            if not current_vertex_ids:
                break

        # for all found actions, add their connected tools to the found actions
        action_vertex_ids: Set[str] = set(vertex_ids_to_keep)
        for action_vertex_id in action_vertex_ids:
            for tool_id in self.get_toolkit().successors(action_vertex_id):
                if (
                    self.get_toolkit().get_action(action_vertex_id)
                    and self.get_toolkit().get_tool(tool_id)
                    and self.get_toolkit().get_score(action_vertex_id, tool_id) >= threshold
                ):
                    vertex_ids_to_keep.add(tool_id)

        toolkit_subgraph: Toolkit = self.get_toolkit().subgraph(list(vertex_ids_to_keep))

        # remove edges that don't meet the threshold
        for u, v in toolkit_subgraph.edges():
            if toolkit_subgraph.get_score(u, v) < threshold:
                toolkit_subgraph.remove_edge(u, v)
        self.visualize(graph=toolkit_subgraph, title="Recommended Toolkit")

        return toolkit_subgraph

    def recommend_tools_actions(
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
        subgraph = self.recommend_subgraph(actions, threshold, hops)
        rec_actions: List[Action] = []
        rec_tools: List[Tool] = []
        for n in subgraph.vertices():
            item: Optional[Union[Action, Tool]] = subgraph.get_action(n) or subgraph.get_tool(n)
            assert item is not None
            if isinstance(item, Action):
                rec_actions.append(item)
            elif isinstance(item, Tool):
                rec_tools.append(item)

        return rec_tools, rec_actions

    def update_action(self, text: str, called_tools: List[Tool]):
        """Update the toolkit graph by reinforcement learning.

        Args:
            text (str): The text of the action
            called_tools (List[Tool]): List of tools that were called in this interaction
        """
        # TODO: simple reinforcement learning implementation
        raise NotImplementedError("This method is not implemented")

    def tune(self, *args: Any, **kwargs: Any) -> Any:
        """Train the toolkit by RL."""
        # TODO: implement the tune method
        raise NotImplementedError("This method is not implemented")

    def visualize(self, graph: Toolkit, title: str, show=True):
        """Visualize the toolkit graph with different colors for actions and tools.

        Args:
            graph (Toolkit): The graph to visualize.
            title (str): Title for the plot.
            show (bool): Whether to show the plot.

        Returns:
            plt.Figure: The plot figure.
        """
        plt.figure(figsize=(12, 8))

        # get vertex positions using spring layout with larger distance and more iterations
        pos = nx.spring_layout(
            graph.get_graph(), k=2, iterations=200
        )  # increase k and iterations for better layout

        # draw vertices
        action_vertices = [n for n in graph.vertices() if graph.get_action(n)]
        tool_vertices = [n for n in graph.vertices() if graph.get_tool(n)]

        # draw action vertices in blue
        nx.draw_networkx_nodes(
            graph.get_graph(),
            pos,
            nodelist=action_vertices,
            node_color="lightblue",
            node_size=2000,
            node_shape="o",
        )

        # draw tool vertices in green
        nx.draw_networkx_nodes(
            graph.get_graph(),
            pos,
            nodelist=tool_vertices,
            node_color="lightgreen",
            node_size=1500,
            node_shape="s",
        )

        # draw edges with different colors and styles for different types
        next_edges = [(u, v) for (u, v) in graph.edges() if graph.get_action(v)]
        call_edges = [(u, v) for (u, v) in graph.edges() if graph.get_tool(v)]

        # draw action-to-action edges in blue with curved arrows
        nx.draw_networkx_edges(
            graph.get_graph(),
            pos,
            edgelist=next_edges,
            edge_color="blue",
            arrows=True,
            arrowsize=35,
            width=2,
        )

        # draw action-to-tool edges in green with different curve style
        nx.draw_networkx_edges(
            graph.get_graph(),
            pos,
            edgelist=call_edges,
            edge_color="green",
            arrows=True,
            arrowsize=35,
            width=1.5,
        )

        # add edge labels (scores) with adjusted positions for curved edges
        edge_labels = {(u, v): f"{graph.get_score(u, v):.2f}" for (u, v) in graph.edges()}

        nx.draw_networkx_edge_labels(
            graph.get_graph(),
            pos,
            edge_labels,
            font_size=8,
            label_pos=0.5,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7},
        )

        # add vertex labels - handle both Action and Tool vertices
        vertex_labels: Dict[str, str] = {}  # vertex id -> action id or tool id
        for n in graph.vertices():
            item: Optional[Union[Action, Tool]] = graph.get_action(n) or graph.get_tool(n)
            assert item is not None
            vertex_labels[n] = item.id

        # draw labels with white background for better visibility
        nx.draw_networkx_labels(
            graph.get_graph(),
            pos,
            vertex_labels,
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
