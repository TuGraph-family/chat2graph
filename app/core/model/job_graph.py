from typing import Dict, List, Optional, Tuple, Union

import networkx as nx  # type: ignore

from app.core.model.graph import Graph
from app.core.model.job import Job
from app.core.model.job_result import JobResult


class JobGraph(Graph):
    """JobGraph is the class to represent the job graph.

    Attributes:
        ...
        _jobs (Dict[str, Job]): The job dictionary (job_id -> job).
        _expert_ids (Dict[str, str]): The expert dictionary (job_id -> expert_id).
        _legacy_jobs (Dict[str, Job]): The legacy job dictionary (job_id -> legacy_job).
        _job_results (Dict[str, JobResult]): The job result dictionary (job_id -> job_result).
    """

    def __init__(self):
        super().__init__()

        # graph vertex properties
        self._jobs: Dict[str, Job] = {}  # job_id -> job
        self._expert_ids: Dict[str, str] = {}  # job_id -> expert_id
        self._legacy_jobs: Dict[str, Job] = {}  # job_id -> legacy_job
        self._job_results: Dict[str, JobResult] = {}  # job_id -> job_result

    def add_vertex(self, id: str, **properties) -> None:
        """Add a vertex to the job graph."""
        self._graph.add_node(id)

        if "job" in properties:
            self._jobs[id] = properties["job"]
        if "expert_id" in properties:
            self._expert_ids[id] = properties["expert_id"]
        if "legacy_job" in properties:
            self._legacy_jobs[id] = properties["legacy_job"]
        if "job_result" in properties:
            self._job_results[id] = properties["job_result"]

    def vertices_data(self) -> List[Tuple[str, Dict[str, Union[Job, str, JobResult, None]]]]:
        """Get the vertices of the job graph with data.

        Returns:
            List[Tuple[str, Dict[str, Union[Job, str, JobResult, None]]]: The vertices with data
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
        """Update current graph with vertices and edges from other graph.

        Args:
            other (Graph): Another JobGraph instance whose vertices and edges will be added to
                this graph.
        """
        # update vertices
        for vertex_id, data in other.vertices_data():
            if vertex_id not in self._graph:
                self._graph.add_node(vertex_id)

            # update vertex properties
            if "job" in data and isinstance(data["job"], Job):
                self._jobs[vertex_id] = data["job"]
            if "expert_id" in data and isinstance(data["expert_id"], str):
                self._expert_ids[vertex_id] = data["expert_id"]
            if "legacy_job" in data and isinstance(data["legacy_job"], Job):
                self._legacy_jobs[vertex_id] = data["legacy_job"]
            if "job_result" in data and isinstance(data["job_result"], JobResult):
                self._job_results[vertex_id] = data["job_result"]

        # update edges
        other_graph = other.get_graph()
        for u, v in other_graph.edges():
            if not self._graph.has_edge(u, v):
                self._graph.add_edge(u, v)

    def remove_vertex(self, id: str) -> None:
        """Remove a vertex from the job graph."""
        self._graph.remove_node(id)

        # please note that, it adds the legacy job back to the graph
        self.set_legacy_job(id)

        # remove vertex properties
        self._jobs.pop(id, None)
        self._expert_ids.pop(id, None)
        self._job_results.pop(id, None)

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
        job_graph._jobs = {id: self._jobs[id] for id in ids if id in self._jobs}  # noqa: W0212
        job_graph._expert_ids = {id: self._expert_ids[id] for id in ids if id in self._expert_ids}  # noqa: W0212
        job_graph._legacy_jobs = {
            id: self._legacy_jobs[id] for id in ids if id in self._legacy_jobs
        }  # noqa: W0212
        job_graph._job_results = {
            id: self._job_results[id] for id in ids if id in self._job_results
        }  # noqa: W0212

        return job_graph

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
