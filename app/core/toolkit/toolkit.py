from typing import Dict, List, Optional, Tuple, Union

import networkx as nx  # type: ignore

from app.core.model.graph import Graph
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

    def __init__(self, graph: Optional[nx.DiGraph] = None) -> None:
        super().__init__(graph=graph)
        self._actions: Dict[str, Action] = {}  # vertex_id -> Action
        self._tools: Dict[str, Tool] = {}  # vertex_id -> Tool
        self._scores: Dict[Tuple[str, str], float] = {}  # (u, v) -> score

    def add_vertex(self, id, **properties) -> None:
        """Add a vertex to the graph."""
        self._graph.add_node(id)

        if isinstance(properties["data"], Action):
            self._actions[id] = properties["data"]
        if isinstance(properties["data"], Tool):
            self._tools[id] = properties["data"]

    def vertices_data(self) -> List[Tuple[str, Dict[str, Union[Action, Tool]]]]:
        """Get the vertices of the toolkit graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Action, Tool]]]: List of vertices with data
            in tuple.
        """
        return [
            (id, {"data": data})
            for id in self._graph.nodes()
            if (data := self.get_action(id) or self.get_tool(id)) is not None
        ]

    def update(self, other: Graph) -> None:
        """Update current graph with vertices and edges from other graph.

        Args:
            other (Graph): Another Toolkit instance whose vertices and edges will be added to this
                graph.
        """
        assert isinstance(other, Toolkit)

        # update vertices
        for vertex_id, data in other.vertices_data():
            if vertex_id not in self._graph:
                self._graph.add_node(vertex_id)

            # update vertex properties
            if "data" in data and isinstance(data["data"], Action):
                self._actions[vertex_id] = data["data"]
            if "data" in data and isinstance(data["data"], Tool):
                self._tools[vertex_id] = data["data"]

        # update edges
        other_graph = other.get_graph()
        for u, v in other_graph.edges():
            if not self._graph.has_edge(u, v):
                self._graph.add_edge(u, v)
                self._scores[(u, v)] = other.get_score(u, v)

    def subgraph(self, ids: List[str]) -> "Toolkit":
        """Get the subgraph of the graph.

        Args:
            ids (List[str]): The vertex ids to include in the subgraph.

        Returns:
            Toolkit: The subgraph.
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

    def remove_vertex(self, id: str) -> None:
        """Remove a vertex from the job graph."""
        # if the id is action's, remove all its tool successors which are only called by this action
        # if the id is tool's which has no successors, just remove it self
        successors = self.successors(id)

        for successor in successors:
            tool: Optional[Tool] = self.get_tool(successor)
            if tool and len(self.predecessors(successor)) == 1:
                self.remove_vertex(successor)

        # remove vertex properties
        self._actions.pop(id, None)
        self._tools.pop(id, None)
        self.remove_vertex(id)

    def get_action(self, id: str) -> Optional[Action]:
        """Get action by vertex id."""
        return self._actions.get(id, None)

    def get_tool(self, id: str) -> Optional[Tool]:
        """Get tool by vertex id."""
        return self._tools.get(id, None)

    def get_score(self, u: str, v: str) -> float:
        """Get the score of an edge."""
        return self._scores.get((u, v), 1.0)

    def set_score(self, u: str, v: str, score: float) -> None:
        """Set the score of an edge."""
        self._scores[(u, v)] = score
