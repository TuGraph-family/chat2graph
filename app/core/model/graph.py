from abc import abstractmethod
from typing import Any, Dict, List, Set, Tuple, Union

import networkx as nx  # type: ignore


class Graph:
    """Graph class represent a graph structure.

    Attributes:
        _graph (nx.DiGraph): The oriented graph to present the dependencies.
    """

    def __init__(self):
        self._graph: nx.DiGraph = nx.DiGraph()  # only vertex ids

    def add_edge(self, u_of_edge: str, v_of_edge: str) -> None:
        """Add an edge to the graph."""
        self._graph.add_edge(u_of_edge, v_of_edge)

    def has_vertex(self, id: str) -> bool:
        """Check if the vertex exists in the graph."""
        return self._graph.has_node(id)

    def vertices(self) -> List[str]:
        """Get the vertices of the graph."""
        return list(self._graph.nodes())

    def edges(self) -> List[Tuple[str, str]]:
        """Get the edges of the graph."""
        return list(self._graph.edges())

    def predecessors(self, id: str) -> List[str]:
        """Get the predecessors of the vertex."""
        return list(self._graph.predecessors(id))

    def successors(self, id: str) -> List[str]:
        """Get the successors of the vertex."""
        return list(self._graph.successors(id))

    def out_degree(self, vertex: str) -> int:
        """Return the number of outgoing edges from the vertex.

        Args:
            vertex: The vertex ID to get the out degree for.

        Returns:
            int: The number of outgoing edges.
        """
        return int(self._graph.out_degree(vertex))

    def vertices_count(self) -> int:
        """Get the number of vertices in the graph."""
        return int(self._graph.number_of_nodes())

    def get_graph(self) -> nx.DiGraph:
        """Get the graph."""
        return self._graph

    def remove_vertices(self, ids: Set[str]) -> None:
        """Remove multiple vertices from the graph.

        Args:
            vertices: List of vertex IDs to remove.
        """
        for id in ids:
            self.remove_vertex(id)

    def remove_edge(self, u_of_edge: str, v_of_edge: str) -> None:
        """Remove an edge from the graph."""
        self._graph.remove_edge(u_of_edge, v_of_edge)

    @abstractmethod
    def add_vertex(self, id: str, **properties) -> None:
        """Add a vertex to the job graph."""

    @abstractmethod
    def vertices_data(self) -> List[Tuple[str, Dict[str, Union[Any]]]]:
        """Get the vertices of the job graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Any]]]]: The vertices with data in tuple.
        """

    @abstractmethod
    def update(self, other: "Graph") -> None:
        """Update current graph with vertices and edges from other graph.

        Args:
            other (Graph): Another graph instance whose vertices and edges will be added to this
                graph.
        """

    @abstractmethod
    def remove_vertex(self, id: str) -> None:
        """Remove a vertex from the graph."""

    @abstractmethod
    def subgraph(self, ids: List[str]) -> Any:
        """Get the subgraph of the graph.

        Args:
            ids (List[str]): The vertex ids to include in the subgraph.

        Returns:
            Graph: The subgraph.
        """
