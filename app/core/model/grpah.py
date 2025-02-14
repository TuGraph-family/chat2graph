from abc import abstractmethod
from typing import Any, Dict, List, Set, Tuple, Union

import networkx as nx  # type: ignore


class Graph:
    """Graph class represent a graph structure.

    Attributes:
        _graph (nx.DiGraph): The oriented graph to present the dependencies.
    """

    def __init__(self):
        self._graph: nx.DiGraph = nx.DiGraph()  # only node ids

    def add_edge(self, u_of_edge: str, v_of_edge: str) -> None:
        """Add an edge to the graph."""
        self._graph.add_edge(u_of_edge, v_of_edge)

    def has_node(self, id: str) -> bool:
        """Check if the node exists in the graph."""
        return self._graph.has_node(id)

    def nodes(self) -> List[str]:
        """Get the nodes of the graph."""
        return list(self._graph.nodes())

    def edges(self) -> List[Tuple[str, str]]:
        """Get the edges of the graph."""
        return list(self._graph.edges())

    def predecessors(self, id: str) -> List[str]:
        """Get the predecessors of the node."""
        return list(self._graph.predecessors(id))

    def successors(self, id: str) -> List[str]:
        """Get the successors of the node."""
        return list(self._graph.successors(id))

    def out_degree(self, node: str) -> int:
        """Return the number of outgoing edges from the node.

        Args:
            node: The node ID to get the out degree for.

        Returns:
            int: The number of outgoing edges.
        """
        return int(self._graph.out_degree(node))

    def number_of_nodes(self) -> int:
        """Get the number of nodes in the graph."""
        return int(self._graph.number_of_nodes())

    def get_graph(self) -> nx.DiGraph:
        """Get the graph."""
        return self._graph

    def remove_nodes(self, ids: Set[str]) -> None:
        """Remove multiple nodes from the graph.

        Args:
            nodes: List of node IDs to remove.
        """
        for id in ids:
            self.remove_node(id)

    def remove_edge(self, u_of_edge: str, v_of_edge: str) -> None:
        """Remove an edge from the graph."""
        self._graph.remove_edge(u_of_edge, v_of_edge)

    @abstractmethod
    def add_node(self, id: str, **properties) -> None:
        """Add a node to the job graph."""

    @abstractmethod
    def nodes_data(self) -> List[Tuple[str, Dict[str, Union[Any]]]]:
        """Get the nodes of the job graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Any]]]]: The nodes with data in tuple.
        """

    @abstractmethod
    def update(self, other: "Graph") -> None:
        """Update current graph with nodes and edges from other graph.

        Args:
            other (Graph): Another JobGraph instance whose nodes and edges will be added to this graph.
        """

    @abstractmethod
    def remove_node(self, id: str) -> None:
        """Remove a node from the graph."""

    @abstractmethod
    def subgraph(self, ids: List[str]) -> Any:
        """Get the subgraph of the graph.

        Args:
            ids (List[str]): The node ids to include in the subgraph.

        Returns:
            Graph: The subgraph.
        """
