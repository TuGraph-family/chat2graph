from typing import Dict, List, Optional, Tuple

import networkx as nx  # type: ignore

from app.core.model.graph import Graph


class JobGraph(Graph):
    """JobGraph is the class to represent the job graph."""

    def __init__(self, graph: Optional[nx.DiGraph] = None) -> None:
        super().__init__(graph=graph)

    def add_vertex(self, id: str, **properties) -> None:
        """Add a vertex to the job graph."""
        self._graph.add_node(id)

    def vertices_data(self) -> List[Tuple[str, Dict]]:
        """Get the vertices of the job graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Job, str, JobResult, None]]]: The vertices with data
            in tuple.
        """
        return [(id, {}) for id in self._graph.nodes()]

    def update(self, other: Graph) -> None:
        """Update current graph with vertices and edges from other graph.

        Args:
            other (Graph): Another JobGraph instance whose vertices and edges will be added to
                this graph.
        """
        # update vertices
        for vertex_id, _ in other.vertices_data():
            if vertex_id not in self._graph:
                self._graph.add_node(vertex_id)

        # update edges
        other_graph = other.get_graph()
        for u, v in other_graph.edges():
            if not self._graph.has_edge(u, v):
                self._graph.add_edge(u, v)

    def remove_vertex(self, id: str) -> None:
        """Remove a vertex from the job graph."""
        self._graph.remove_node(id)

    def subgraph(self, ids: List[str]) -> "JobGraph":
        """Get the subgraph of the graph.

        Args:
            ids (List[str]): The vertex ids to include in the subgraph.

        Returns:
            JobGraph: The subgraph.
        """
        job_graph = JobGraph()

        subgraph_view: nx.DiGraph = self._graph.subgraph(ids)
        job_graph._graph = subgraph_view.copy()  # noqa: W0212

        return job_graph
