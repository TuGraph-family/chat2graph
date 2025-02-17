import time
from typing import Dict, List, Optional, Set

import networkx as nx  # type: ignore

from app.core.agent.expert import Expert
from app.core.common.singleton import Singleton
from app.core.common.type import JobStatus
from app.core.model.job import Job
from app.core.model.job_graph import JobGraph
from app.core.model.job_result import JobResult
from app.core.model.message import TextMessage
from app.core.service.agent_service import AgentService


class JobService(metaclass=Singleton):
    """Job service"""

    def __init__(self):
        self._job_graphs: Dict[str, JobGraph] = {}  # original_job_id -> nx.DiGraph

    async def query_job_result(self, job_id: str) -> JobResult:
        """Query the result of the multi-agent system by original job id."""
        if job_id not in self._job_graphs:
            raise ValueError(
                f"Job with ID {job_id} not found in the job registry, or not yet submitted."
            )

        # query the state to get the job execution information
        job_graph = self.get_job_graph(job_id)

        # get the tail vertices of the job graph (DAG)
        tail_vertices: List[str] = [
            vertex for vertex in job_graph.vertices() if job_graph.out_degree(vertex) == 0
        ]

        # combine the content of the job results from the tail vertices
        mutli_agent_payload = ""
        for tail_vertex in tail_vertices:
            job_result: Optional[JobResult] = job_graph.get_job_result(tail_vertex)
            if not job_result:
                chat_message = TextMessage(
                    payload="The job is not completed yet.",
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                )
                return JobResult(
                    job_id=job_id,
                    status=JobStatus.RUNNING,
                    duration=0,  # TODO: calculate the duration
                    tokens=0,  # TODO: calculate the tokens
                    result=chat_message,
                )
            mutli_agent_payload += job_result.result.get_payload() + "\n"

        # parse the multi-agent result
        job_result = JobResult(
            job_id=job_id,
            status=JobStatus.FINISHED,
            duration=0,  # TODO: calculate the duration
            tokens=0,  # TODO: calculate the tokens
            result=TextMessage(
                payload=mutli_agent_payload,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )

        return job_result

    async def execute_job(self, job: Job) -> None:
        """Execute the job."""
        # submit the job by self
        initial_job_graph: JobGraph = JobGraph()
        initial_job_graph.add_vertex(id=job.id, job=job)
        self.set_job_graph(job_id=job.id, job_graph=initial_job_graph)

        # submit the job to the leader
        agent_service: AgentService = AgentService.instance
        executed_job_graph = await agent_service.leader.execute_job(job=job)

        # replace the subgraph in the job service
        self.replace_subgraph(
            original_job_id=job.id,
            new_subgraph=executed_job_graph,
            old_subgraph=self.get_job_graph(job.id),
        )

    def get_job_graph(self, job_id: str) -> JobGraph:
        """Get the job graph by the inital job id."""
        if job_id not in self._job_graphs:
            job_graph = JobGraph()
            self._job_graphs[job_id] = job_graph
            return job_graph
        return self._job_graphs[job_id]

    def set_job_graph(self, job_id: str, job_graph: JobGraph) -> None:
        """Set the job graph by the inital job id."""
        self._job_graphs[job_id] = job_graph

    def add_job(
        self,
        original_job_id: str,
        job: Job,
        expert: Expert,
        predecessors: Optional[List[Job]] = None,
        successors: Optional[List[Job]] = None,
    ) -> None:
        """Assign a job to an expert and return the expert instance."""

        # add job to the jobs graph
        job_graph = self.get_job_graph(original_job_id)
        job_graph.add_vertex(job.id, job=job, expert_id=expert.get_id())

        if not predecessors:
            predecessors = []
        if not successors:
            successors = []
        for predecessor in predecessors:
            job_graph.add_edge(predecessor.id, job.id)
        for successor in successors:
            job_graph.add_edge(job.id, successor.id)

        self._job_graphs[original_job_id] = job_graph

    def remove_job(self, original_job_id: str, job_id: str) -> None:
        """Remove a Job from the Job registry."""
        job_graph = self.get_job_graph(original_job_id)
        job_graph.remove_vertex(job_id)
        self._job_graphs[original_job_id] = job_graph

    def get_job(self, original_job_id: str, job_id: str) -> Job:
        """Get a Job from the Job registry."""
        return self.get_job_graph(original_job_id).get_job(job_id)

    def replace_subgraph(
        self,
        original_job_id: str,
        new_subgraph: JobGraph,
        old_subgraph: Optional[JobGraph] = None,
    ) -> None:
        """Replace a subgraph in the jobs DAG with a new subgraph.

        This method replaces a connected subgraph of the jobs DAG with a new subgraph.

        The old subgraph must satisfy these requirements:
            1. It must be a valid subgraph of the current jobs DAG
            2. It must have exactly one vertex that connects to the rest of the DAG as input
            (the entry vertex)
            3. It must have exactly one vertex that connects to the rest of the DAG as output
            (the exit vertex)

        The replacement process:
            1. Identifies the entry and exit vertices of the old subgraph
            2. Collects connections between the subgraph and the rest of the DAG
            3. Removes the old subgraph
            4. Adds the new subgraph
            5. Reconnects using the first vertex of the new subgraph as entry
            and the last vertex as exit (based on topological sort)

        Example:
            Consider a DAG:  A -> B -> C -> D
                              \-> E -/

            To replace subgraph {B} with new vertices {X, Y}:
                old_subgraph = DAG containing vertices {B}
                new_subgraph = DAG containing vertices {X, Y}

            Result: A -> X -> Y -> C -> D
                     \ ->   E    -/

        Args:
            original_job_id (str): The session ID of the jobs DAG to update.
            new_subgraph (JobGraph): The new subgraph to insert. Must have all vertices containing
                'job' and 'expert_id' attributes.
            old_subgraph (Optional[JobGraph]): The subgraph to be replaced. Must be a connected
                component of the current jobs DAG with exactly one entry and one exit vertex.
        """
        # validate
        for vertex, data in new_subgraph.vertices_data():
            if "job" not in data or not isinstance(data["job"], Job):
                raise ValueError(f"Vertex {vertex} missing required 'job' attribute")
            if "expert_id" not in data or not isinstance(data["expert_id"], str):
                raise ValueError(f"Vertex {vertex} missing required 'expert_id' attribute")

        job_graph: JobGraph = self.get_job_graph(original_job_id)

        if not old_subgraph:
            job_graph.update(new_subgraph)
            return

        old_subgraph_vertices: Set[str] = set(old_subgraph.vertices())
        entry_vertices: List[str] = []
        exit_vertices: List[str] = []

        # find the entry and exit vertex of the job_graph
        for vertex in old_subgraph_vertices:
            entry_vertices.extend(
                vertex
                for pred in job_graph.predecessors(vertex)
                if pred not in old_subgraph_vertices
            )
            exit_vertices.extend(
                vertex for succ in job_graph.successors(vertex) if succ not in old_subgraph_vertices
            )

        # validate the subgraph has exactly one entry and one exit vertex
        if len(entry_vertices) > 1 or len(exit_vertices) > 1:
            raise ValueError("Subgraph must have no more than one entry and one exit vertex")
        entry_vertex = entry_vertices[0] if entry_vertices else None
        exit_vertex = exit_vertices[0] if exit_vertices else None

        # collect all edges pointing to and from the old subgraph
        predecessors = (
            [
                vertex
                for vertex in job_graph.predecessors(entry_vertex)
                if vertex not in old_subgraph_vertices
            ]
            if entry_vertex
            else []
        )
        successors = (
            [
                vertex
                for vertex in job_graph.successors(exit_vertex)
                if vertex not in old_subgraph_vertices
            ]
            if exit_vertex
            else []
        )

        # remove old subgraph
        job_graph.remove_vertices(old_subgraph_vertices)

        # add the new subgraph without connecting it to the rest of the graph
        job_graph.update(new_subgraph)

        # connect the new subgraph with the rest of the graph
        topological_sorted_vertices = list(nx.topological_sort(new_subgraph.get_graph()))
        head_vertex = topological_sorted_vertices[0]
        tail_vertex = topological_sorted_vertices[-1]
        for predecessor in predecessors:
            job_graph.add_edge(predecessor, head_vertex)
        for successor in successors:
            job_graph.add_edge(tail_vertex, successor)

        self._job_graphs[original_job_id] = job_graph
