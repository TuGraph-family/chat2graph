from typing import Any, Dict, List, Optional, Set, Tuple, Union

from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import networkx as nx  # type: ignore

from app.core.model.grpah import Graph
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool


class Toolkit(Graph):
    """The toolkit is a graph of actions and tools.

    In the toolkit graph, the actions are connected to the tools:
        Action --Next--> Action
        Action --Call--> Tool

    Attributes:
        _graph (nx.DiGraph): The oriented graph to present the dependencies.
        _actions (Dict[str, Action]): The actions in the graph.
        _tools (Dict[str, Tool]): The tools in the graph.
        _scores (Dict[Tuple[str, str], float]): The scores of the edges in the graph.
    """

    def __init__(self):
        super().__init__()
        self._actions: Dict[str, Action] = {}  # node_id -> Action
        self._tools: Dict[str, Tool] = {}  # node_id -> Tool
        self._scores: Dict[Tuple[str, str], float] = {}  # (u, v) -> score

    def add_node(self, id, **properties) -> None:
        """Add a node to the graph."""
        self._graph.add_node(id)

        if isinstance(properties["data"], Action):
            self._actions[id] = properties["data"]
        if isinstance(properties["data"], Tool):
            self._tools[id] = properties["data"]

    def nodes_data(self) -> List[Tuple[str, Dict[str, Union[Action, Tool]]]]:
        """Get the nodes of the toolkit graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Action, Tool]]]: List of nodes with data
            in tuple.
        """
        return [
            (
                id,
                {
                    "data": self._actions.get(id, None) or self._tools.get(id, None),
                },
            )
            for id in self._graph.nodes()
        ]

    def update(self, other: Graph) -> None:
        """Update current graph with nodes and edges from other graph.

        Args:
            other (Graph): Another Toolkit instance whose nodes and edges will be added to this
                graph.
        """
        assert isinstance(other, Toolkit)

        # update nodes
        for node_id, data in other.nodes_data():
            if node_id not in self._graph:
                self._graph.add_node(node_id)

            # update node properties
            if "data" in data and isinstance(data["data"], Action):
                self._actions[node_id] = data["data"]
            if "data" in data and isinstance(data["data"], Tool):
                self._tools[node_id] = data["data"]

        # update edges
        other_graph = other.get_graph()
        for u, v in other_graph.edges():
            if not self._graph.has_edge(u, v):
                self._graph.add_edge(u, v)
                self._scores[(u, v)] = other.get_score(u, v)

    def subgraph(self, ids: List[str]) -> Graph:
        """Get the subgraph of the graph.

        Args:
            ids (List[str]): The node ids to include in the subgraph.

        Returns:
            Graph: The subgraph.
        """
        toolkit_graoh = Toolkit()

        subgraph_view: nx.DiGraph = self._graph.subgraph(ids)
        toolkit_graoh._graph = subgraph_view.copy()  # noqa: W0212
        toolkit_graoh._actions = {id: self._actions[id] for id in ids if id in self._actions}  # noqa: W0212
        toolkit_graoh._tools = {id: self._tools[id] for id in ids if id in self._tools}  # noqa: W0212
        toolkit_graoh._scores = {
            (u, v): self._scores[(u, v)]
            for u, v in toolkit_graoh._graph.edges()
            if (u, v) in self._scores
        }  # noqa: W0212

        return toolkit_graoh

    def remove_node(self, id: str) -> None:
        """Remove a node from the job graph."""
        # if the id is action's, remove all its tool successors which are only called by this action
        # if the id is tool's which has no successors, just remove it self
        successors = self.successors(id)

        for successor in successors:
            tool: Optional[Tool] = self.get_tool(successor)
            if tool and len(self.predecessors(successor)) == 1:
                self.remove_node(successor)

        # remove node properties
        self._actions.pop(id, None)
        self._tools.pop(id, None)
        self.remove_node(id)

    def get_action(self, id: str) -> Optional[Action]:
        """Get action by node id."""
        return self._actions.get(id, None)

    def get_tool(self, id: str) -> Optional[Tool]:
        """Get tool by node id."""
        return self._tools.get(id, None)

    def get_score(self, u: str, v: str) -> float:
        """Get the score of an edge."""
        return self._scores.get((u, v), 1.0)

    def set_score(self, u: str, v: str, score: float) -> None:
        """Set the score of an edge."""
        self._scores[(u, v)] = score


class ToolkitService:
    """The toolkit service provides functionalities for the toolkit."""

    def __init__(self, toolkit: Optional[Toolkit] = None):
        # it manages one toolkit for now, but can be extended to manage multiple toolkits
        self._toolkit = toolkit or Toolkit()

    def get_toolkit(self) -> Toolkit:
        """Get the current toolkit."""
        return self._toolkit

    def with_store(self, store_type: Any) -> "ToolkitService":
        """Use the store for the toolkit."""
        # TODO: implement the persistent storage for the toolkit

    def add_tool(self, tool: Tool, connected_actions: List[tuple[Action, float]]):
        """Add tool to toolkit graph. Action --Call--> Tool.

        Args:
            tool (Tool): The tool to be added
            connected_actions (List[tuple[Action, float]]): List of tuples (action, score) that
                call this tool
        """
        has_connected_actions = False
        # add tool node if not exists
        if tool.id not in self._toolkit.nodes():
            self._toolkit.add_node(tool.id, data=tool)

        # add edges from actions to tool
        for action, score in connected_actions:
            if action.id in self._toolkit.nodes():
                self._toolkit.add_edge(action.id, tool.id)
                self._toolkit.set_score(action.id, tool.id, score)
                has_connected_actions = True
            else:
                print(f"warning: Action {action.id} not in the toolkit graph")

        if not has_connected_actions:
            print(f"warning: Tool {tool.id} has no connected actions")
            self._toolkit.remove_node(tool.id)

    def add_action(
        self,
        action: Action,
        next_actions: List[tuple[Action, float]],
        prev_actions: List[tuple[Action, float]],
    ) -> None:
        """Add action to the toolkit graph. Action --Next--> Action.

        Args:
            action (Action): The action to be added
            next_actions (List[tuple[Action, float]]): List of tuples (action, score) that follow
                this action
            prev_actions (List[tuple[Action, float]]): List of tuples (action, score) that precede
                this action
        """
        # add action node if not exists
        if action.id not in self._toolkit.nodes():
            self._toolkit.add_node(action.id, data=action)

        # add edges to next actions
        for next_action, score in next_actions:
            if next_action.id in self._toolkit.nodes():
                self._toolkit.add_edge(action.id, next_action.id)
                self._toolkit.set_score(action.id, next_action.id, score)

        # add edges from previous actions
        for prev_action, score in prev_actions:
            if prev_action.id in self._toolkit.nodes():
                self._toolkit.add_edge(prev_action.id, action.id)
                self._toolkit.set_score(prev_action.id, action.id, score)

    def get_action(self, action_id: str) -> Action:
        """Get action from the toolkit graph."""
        action: Optional[None] = self._toolkit.get_action(action_id)
        if not action:
            raise ValueError(f"Action {action_id} not found in the toolkit graph")
        return action

    def remove_tool(self, tool_id: str):
        """Remove tool from the toolkit graph."""
        self._toolkit.remove_node(tool_id)

    def remove_action(self, action_id: str):
        """Remove action from the toolkit graph."""
        self._toolkit.remove_node(action_id)

    async def recommend_subgraph(
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
        # get initial action node ids
        node_ids_to_keep: Set[str] = {
            action.id for action in actions if action.id in self._toolkit.nodes()
        }

        # do BFS to get all action node ids within hops
        current_node_ids = node_ids_to_keep.copy()
        for _ in range(hops):
            next_node_ids: Set[str] = set()
            for node_id in current_node_ids:
                # find next actions connected with score >= threshold
                for neighbor_id in self._toolkit.successors(node_id):
                    if (
                        self._toolkit.get_action(node_id)
                        and self._toolkit.get_action(neighbor_id)
                        and self._toolkit.get_score(node_id, neighbor_id) >= threshold
                    ):
                        next_node_ids.add(neighbor_id)
                        node_ids_to_keep.add(neighbor_id)

            current_node_ids = next_node_ids
            if not current_node_ids:
                break

        # for all found actions, add their connected tools to the found actions
        action_node_ids: Set[str] = set(node_ids_to_keep)

        for action_node_id in action_node_ids:
            for tool_id in self._toolkit.successors(action_node_id):
                if (
                    self._toolkit.get_action(action_node_id)
                    and self._toolkit.get_tool(tool_id)
                    and self._toolkit.get_score(action_node_id, tool_id) >= threshold
                ):
                    node_ids_to_keep.add(tool_id)

        toolkit_subgraph: Toolkit = self._toolkit.subgraph(list(node_ids_to_keep))

        # remove edges that don't meet the threshold
        for u, v in toolkit_subgraph.edges():
            if toolkit_subgraph.get_score(u, v) < threshold:
                toolkit_subgraph.remove_edge(u, v)
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
        actions: List[Action] = []
        tools: List[Tool] = []
        for n in subgraph.nodes():
            item: Optional[Union[Action, Tool]] = subgraph.get_action(n) or subgraph.get_tool(n)
            assert item is not None
            if isinstance(item, Action):
                actions.append(item)
            elif isinstance(item, Tool):
                tools.append(item)

        return tools, actions

    async def update_action(self, text: str, called_tools: List[Tool]):
        """Update the toolkit graph by reinforcement learning.

        Args:
            text (str): The text of the action
            called_tools (List[Tool]): List of tools that were called in this interaction
        """
        # TODO: simple reinforcement learning implementation
        # Increase weight of edges leading to successful tool calls

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

        # get node positions using spring layout with larger distance and more iterations
        pos = nx.spring_layout(
            graph.get_graph(), k=2, iterations=200
        )  # increase k and iterations for better layout

        # draw nodes
        action_nodes = [n for n in graph.nodes() if graph.get_action(n)]
        tool_nodes = [n for n in graph.nodes() if graph.get_tool(n)]

        # draw action nodes in blue
        nx.draw_networkx_nodes(
            graph.get_graph(),
            pos,
            nodelist=action_nodes,
            node_color="lightblue",
            node_size=2000,
            node_shape="o",
        )

        # draw tool nodes in green
        nx.draw_networkx_nodes(
            graph.get_graph(),
            pos,
            nodelist=tool_nodes,
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

        # add node labels - handle both Action and Tool nodes
        node_labels: Dict[str, str] = {}  # node id -> action id or tool id
        for n in graph.nodes():
            item: Optional[Union[Action, Tool]] = graph.get_action(n) or graph.get_tool(n)
            assert item is not None
            node_labels[n] = item.id

        # draw labels with white background for better visibility
        nx.draw_networkx_labels(
            graph.get_graph(),
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
