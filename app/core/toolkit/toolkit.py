from typing import Dict, List, Optional, Tuple, Union

import networkx as nx  # type: ignore

from app.core.model.graph import Graph
from app.core.toolkit.action import Action
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_group import ToolGroup


class Toolkit(Graph):
    """The toolkit is a graph of actions and tools.

    In the toolkit graph, the actions are connected to the tools:
        Action --Next--> Action
        Action --Call--> Tool
        ToolGroup --Group_Has_Tool--> Tool

    Attributes:
        _graph (nx.DiGraph): The oriented graph to present the dependencies.
        _actions (Dict[str, Action]): The actions in the graph.
        _tools (Dict[str, Tool]): The tools in the graph.
        _tool_groups (Dict[str, ToolGroup]): The tool groups in the graph.
        _scores (Dict[Tuple[str, str], float]): The scores of the edges in the graph.
    """

    def __init__(self, graph: Optional[nx.DiGraph] = None) -> None:
        super().__init__(graph=graph)
        self._actions: Dict[str, Action] = {}  # vertex_id -> Action
        self._tools: Dict[str, Tool] = {}  # vertex_id -> Tool
        self._tool_groups: Dict[str, ToolGroup] = {}  # vertex_id -> ToolGroup
        self._scores: Dict[Tuple[str, str], float] = {}  # (u, v) -> score

    def add_vertex(self, id, **properties) -> None:
        """Add a vertex to the graph."""
        self._graph.add_node(id)

        if isinstance(properties["data"], Action):
            self._actions[id] = properties["data"]
        if isinstance(properties["data"], Tool):
            self._tools[id] = properties["data"]
        if isinstance(properties["data"], ToolGroup):
            self._tool_groups[id] = properties["data"]

    def vertices_data(self) -> List[Tuple[str, Dict[str, Union[Action, Tool, ToolGroup]]]]:
        """Get the vertices of the toolkit graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Action, Tool, ToolGroup]]]: List of vertices with data
            in tuple.
        """
        return [
            (id, {"data": data})
            for id in self._graph.nodes()
            if (data := self.get_action(id) or self.get_tool(id) or self.get_tool_group(id))
            is not None
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
            if "data" in data and isinstance(data["data"], ToolGroup):
                self._tool_groups[vertex_id] = data["data"]

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
        toolkit_graph = Toolkit()

        subgraph_view: nx.DiGraph = self._graph.subgraph(ids)
        toolkit_graph._graph = subgraph_view.copy()  # noqa: W0212
        toolkit_graph._actions = {id: self._actions[id] for id in ids if id in self._actions}  # noqa: W0212
        toolkit_graph._tools = {id: self._tools[id] for id in ids if id in self._tools}  # noqa: W0212
        toolkit_graph._tool_groups = {
            id: self._tool_groups[id] for id in ids if id in self._tool_groups
        }  # noqa: W0212
        toolkit_graph._scores = {
            (u, v): self._scores[(u, v)]
            for u, v in toolkit_graph._graph.edges()
            if (u, v) in self._scores
        }  # noqa: W0212

        return toolkit_graph

    def remove_vertex(self, id: str) -> None:
        """Remove a vertex from the job graph, handling cascading deletions correctly."""
        if not self._graph.has_node(id):
            return

        item = self.get_action(id) or self.get_tool(id) or self.get_tool_group(id)

        if isinstance(item, Action):
            successors_copy = list(self.successors(id))
            for successor_id in successors_copy:
                tool: Optional[Tool] = self.get_tool(successor_id)
                # if this action is the *only* predecessor of the tool, remove the tool
                if tool and len(list(self.predecessors(successor_id))) == 1:
                    # cascade the delete to the orphaned tool.
                    self.remove_vertex(successor_id)

            self._actions.pop(id, None)

        elif isinstance(item, Tool):
            # when a tool is removed, we need to cascade to the parent ToolGroup,
            # if the tool is the only child

            for predecessor_id in self.predecessors(id):
                tool_group: Optional[ToolGroup] = self.get_tool_group(predecessor_id)
                if tool_group and len(list(self.successors(predecessor_id))) == 1:
                    # if this tool is the only child of the ToolGroup, remove the ToolGroup
                    self._tool_groups.pop(predecessor_id, None)
                    self._graph.remove_node(predecessor_id)

            self._tools.pop(id, None)

        elif isinstance(item, ToolGroup):
            # when a ToolGroup is removed, it cascades to all its children (tools)
            successors_copy = list(self.successors(id))
            for tool_id in successors_copy:
                self.remove_vertex(tool_id)

            self._tool_groups.pop(id, None)

        # final, unified removal from the graph object
        if self._graph.has_node(id):
            self._graph.remove_node(id)

    def get_action(self, id: str) -> Optional[Action]:
        """Get action by vertex id."""
        action = self._actions.get(id, None)
        if action is not None:
            return action.copy()
        return None

    def get_tool(self, id: str) -> Optional[Tool]:
        """Get tool by vertex id."""
        tool = self._tools.get(id, None)
        if tool is not None:
            return tool.copy()
        return None

    def get_tool_group(self, id: str) -> Optional[ToolGroup]:
        """Get tool group by vertex id."""
        return self._tool_groups.get(id, None)

    def get_score(self, u: str, v: str) -> float:
        """Get the score of an edge."""
        return self._scores.get((u, v), 1.0)

    def set_score(self, u: str, v: str, score: float) -> None:
        """Set the score of an edge."""
        self._scores[(u, v)] = score
