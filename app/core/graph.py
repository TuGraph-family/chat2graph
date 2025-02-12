from abc import abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import networkx as nx  # type: ignore

from app.agent.job import Job
from app.agent.job_result import JobResult


class Graph:
    """Graph is the dataclass to represent the graph.

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

    def remove_nodes_from(self, ids: Set[str]) -> None:
        """Remove multiple nodes from the graph.

        Args:
            nodes: List of node IDs to remove.
        """
        for id in ids:
            self.remove_node(id)

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
            other: Another JobGraph instance whose nodes and edges will be added to this graph.
        """

    @abstractmethod
    def remove_node(self, id: str) -> None:
        """Remove a node from the graph.

        Args:
            node: The node ID to remove.
        """


class JobGraph(Graph):
    """JobGraph is the dataclass to represent the job graph.

    Attributes:
        ...
        _jobs (Dict[str, Job]): The job dictionary (job_id -> job).
        _expert_ids (Dict[str, str]): The expert dictionary (job_id -> expert_id).
        _legacy_jobs (Dict[str, Job]): The legacy job dictionary (job_id -> legacy_job).
        _job_results (Dict[str, JobResult]): The job result dictionary (job_id -> job_result).
    """

    def __init__(self):
        super().__init__()

        # graph node properties
        self._jobs: Dict[str, Job] = {}  # job_id -> job
        self._expert_ids: Dict[str, str] = {}  # job_id -> expert_id
        self._legacy_jobs: Dict[str, Job] = {}  # job_id -> legacy_job
        self._job_results: Dict[str, JobResult] = {}  # job_id -> job_result

    def add_node(self, id: str, **properties) -> None:
        """Add a node to the job graph."""
        self._graph.add_node(id)

        if "job" in properties:
            self._jobs[id] = properties["job"]
        if "expert_id" in properties:
            self._expert_ids[id] = properties["expert_id"]
        if "legacy_job" in properties:
            self._legacy_jobs[id] = properties["legacy_job"]
        if "job_result" in properties:
            self._job_results[id] = properties["job_result"]

    def nodes_data(self) -> List[Tuple[str, Dict[str, Union[Job, str, JobResult, None]]]]:
        """Get the nodes of the job graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Job, str, JobResult, None]]]: The nodes with data
            in tuple.
        """
        return [
            (
                id,
                {
                    "job": self.get_job(id),
                    "expert_id": self.get_expert_id(id),
                    "legacy_job": self.get_legacy_job(id),
                    "job_result": self.get_job_result(id),
                },
            )
            for id in self._graph.nodes()
        ]

    def update(self, other: Graph) -> None:
        """Update current graph with nodes and edges from other graph.

        Args:
            other: Another JobGraph instance whose nodes and edges will be added to this graph.
        """
        # update nodes
        for node_id, data in other.nodes_data():
            if node_id not in self._graph:
                self._graph.add_node(node_id)

            # update node properties
            if "job" in data and isinstance(data["job"], Job):
                self._jobs[node_id] = data["job"]
            if "expert_id" in data and isinstance(data["expert_id"], str):
                self._expert_ids[node_id] = data["expert_id"]
            if "legacy_job" in data and isinstance(data["legacy_job"], Job):
                self._legacy_jobs[node_id] = data["legacy_job"]
            if "job_result" in data and isinstance(data["job_result"], JobResult):
                self._job_results[node_id] = data["job_result"]

        # update edges
        other_graph = other.get_graph()
        for u, v in other_graph.edges():
            if not self._graph.has_edge(u, v):
                self._graph.add_edge(u, v)

    def remove_node(self, id: str) -> None:
        """Remove a node from the job graph.

        Args:
            node: The node ID to remove.
        """
        self._graph.remove_node(id)

        # please note that, it adds the legacy job back to the graph
        self.set_legacy_job(id)

        # remove node properties
        self._jobs.pop(id, None)
        self._expert_ids.pop(id, None)
        self._job_results.pop(id, None)

    def get_job(self, id: str) -> Job:
        """Return the job by id."""
        if id not in self._jobs:
            raise ValueError(f"Job with id {id} does not exist.")
        return self._jobs[id]

    def get_expert_id(self, id: str) -> str:
        """Return the expert id by job id."""
        if id not in self._expert_ids:
            raise ValueError(f"Expert with id {id} does not exist.")
        return self._expert_ids[id]

    def get_legacy_job(self, id: str) -> Optional[Job]:
        """Return the legacy id by job id."""
        return self._legacy_jobs.get(id, None)

    def get_job_result(self, id: str) -> Optional[JobResult]:
        """Return the job result by job id."""
        return self._job_results.get(id, None)

    def set_legacy_job(self, id: str) -> None:
        """Set the legacy job. Please note that, it dosen't remove the legacy job from the graph."""
        self._legacy_jobs[id] = self._jobs[id]

    def set_job_result(self, id: str, job_result: JobResult) -> None:
        """Set the job result by job id."""
        self._job_results[id] = job_result
