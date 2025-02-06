import time
from typing import Dict, List, Optional, Set

import networkx as nx  # type: ignore

from app.agent.expert import Expert
from app.agent.graph import JobGraph
from app.agent.job import Job
from app.agent.job_result import JobResult
from app.agent.leader_state import LeaderState
from app.common.singleton import Singleton
from app.common.type import JobStatus
from app.memory.message import TextMessage


class JobManager(metaclass=Singleton):
    """Job manager"""

    def __init__(self):
        self._job_graphs: Dict[str, JobGraph] = {}  # original_job_id -> nx.DiGraph
        self._legacy_jobs: Dict[str, Job] = {}  # legacy_id -> job

        # TODO: merge the job results to the job graph
        self._job_results: Dict[str, JobResult] = {}  # job_id -> job_result

    async def query_job_result(self, job_id: str) -> JobResult:
        """Query the result of the multi-agent system."""
        if job_id not in self._job_graphs:
            raise ValueError(f"Job with ID {job_id} not found in the job registry.")
        if job_id in self._job_results:
            return self._job_results[job_id]

        # query the state to get the job execution information
        job_graph = self.get_job_graph(job_id)

        # get the tail nodes of the job graph (DAG)
        tail_nodes: List[str] = [
            node for node in job_graph.nodes() if job_graph.out_degree(node) == 0
        ]
        mutli_agent_content = ""
        for tail_node in tail_nodes:
            job_result: Optional[JobResult] = job_graph.get_job_result(tail_node)
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
            mutli_agent_content += job_result.result.get_payload() + "\n"

        # parse the multi-agent result
        chat_message = TextMessage(
            payload=mutli_agent_content,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        job_result = JobResult(
            job_id=job_id,
            status=JobStatus.FINISHED,
            duration=0,  # TODO: calculate the duration
            tokens=0,  # TODO: calculate the tokens
            result=chat_message,
        )

        # update the job result in the job results registry
        self._job_results[job_id] = job_result

        return job_result

    def get_job_graph(self, job_id: str) -> JobGraph:
        """Get the job graph."""
        if job_id not in self._job_graphs:
            job_graph = JobGraph()
            self._job_graphs[job_id] = job_graph
            return job_graph
        return self._job_graphs[job_id]

    def set_job_graph(self, job_id: str, job_graph: JobGraph) -> None:
        """Set the job graph."""
        self._job_graphs[job_id] = job_graph

    def update_legacy_job(self, legacy_job: Job) -> None:
        """Update the legacy job."""
        self._legacy_jobs[legacy_job.id] = legacy_job

    def add_job(
        self,
        original_job_id: str,
        job: Job,
        expert_name: str,
        predecessors: Optional[List[Job]] = None,
        successors: Optional[List[Job]] = None,
    ) -> Expert:
        """Assign a job to an expert and return the expert instance."""
        expert = LeaderState().get_expert_by_name(expert_name)

        # add job to the jobs graph
        job_graph = self.get_job_graph(original_job_id)
        job_graph.add_node(job.id, job=job, expert_id=expert.get_id())

        if not predecessors:
            predecessors = []
        if not successors:
            successors = []
        for predecessor in predecessors:
            job_graph.add_edge(predecessor.id, job.id)
        for successor in successors:
            job_graph.add_edge(job.id, successor.id)

        self._job_graphs[original_job_id] = job_graph

        return expert

    def remove_job(self, original_job_id: str, job_id: str) -> None:
        """Remove a Job from the Job registry."""
        job_graph = self.get_job_graph(original_job_id)
        job_graph.remove_node(job_id)
        self._job_graphs[original_job_id] = job_graph

    def get_job(self, original_job_id: str, job_id: str) -> Job:
        """Get a Job from the Job registry."""
        return self.get_job_graph(original_job_id).get_job(job_id)

    def get_expert_id_by_job_id(self, original_job_id: str, job_id: str) -> Expert:
        """Get an expert from the expert registry."""
        return LeaderState().get_expert_by_id(
            self.get_job_graph(original_job_id).get_expert_id(job_id)
        )

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
            2. It must have exactly one node that connects to the rest of the DAG as input
            (the entry node)
            3. It must have exactly one node that connects to the rest of the DAG as output
            (the exit node)

        The replacement process:
            1. Identifies the entry and exit nodes of the old subgraph
            2. Collects connections between the subgraph and the rest of the DAG
            3. Removes the old subgraph
            4. Adds the new subgraph
            5. Reconnects using the first node of the new subgraph as entry
            and the last node as exit (based on topological sort)

        Example:
            Consider a DAG:  A -> B -> C -> D
                              \-> E -/

            To replace subgraph {B} with new nodes {X, Y}:
                old_subgraph = DAG containing nodes {B}
                new_subgraph = DAG containing nodes {X, Y}

            Result: A -> X -> Y -> C -> D
                     \ ->   E    -/

        Args:
            original_job_id (str): The session ID of the jobs DAG to update.
            new_subgraph (JobGraph): The new subgraph to insert. Must have all nodes containing
                'job' and 'expert_id' attributes.
            old_subgraph (Optional[JobGraph]): The subgraph to be replaced. Must be a connected
                component of the current jobs DAG with exactly one entry and one exit node.
        """
        # validate
        for node, data in new_subgraph.nodes_data():
            if "job" not in data or not isinstance(data["job"], Job):
                raise ValueError(f"Node {node} missing required 'job' attribute")
            if "expert_id" not in data or not isinstance(data["expert_id"], str):
                raise ValueError(f"Node {node} missing required 'expert_id' attribute")

        job_graph: JobGraph = JobManager().get_job_graph(original_job_id)

        if not old_subgraph:
            job_graph.update(new_subgraph)
            return

        old_subgraph_nodes: Set[str] = set(old_subgraph.nodes())
        entry_nodes: List[str] = []
        exit_nodes: List[str] = []

        # find the entry and exit node of the old subgraph
        for node in old_subgraph_nodes:
            _predecessors = list(job_graph.predecessors(node))
            for _predecessor in _predecessors:
                if _predecessor not in old_subgraph_nodes:
                    entry_nodes.append(node)

            _successors = list(job_graph.successors(node))
            for _successor in _successors:
                if _successor not in old_subgraph_nodes:
                    exit_nodes.append(node)

            JobManager().update_legacy_job(old_subgraph.get_job(node))

        if len(entry_nodes) != 1 or len(exit_nodes) != 1:
            raise ValueError("Subgraph must have exactly one entry node and one exit node.")
        entry_node = entry_nodes[0]
        exit_node = exit_nodes[0]

        # collect all edges pointing to and from the old subgraph
        predecessors = []
        for node in job_graph.predecessors(entry_node):
            if node not in old_subgraph_nodes:
                predecessors.append(node)
        successors = []
        for node in job_graph.successors(exit_node):
            if node not in old_subgraph_nodes:
                successors.append(node)

        # remove old subgraph
        job_graph.remove_nodes_from(old_subgraph_nodes)

        # add the new subgraph without connecting it to the rest of the graph
        job_graph.update(new_subgraph)

        # connect the new subgraph with the rest of the graph
        _topological_sorted_nodes = list(nx.topological_sort(new_subgraph.get_graph()))
        head_node = _topological_sorted_nodes[0]
        tail_node = _topological_sorted_nodes[-1]
        for predecessor in predecessors:
            job_graph.add_edge(predecessor, head_node)
        for successor in successors:
            job_graph.add_edge(tail_node, successor)

        self._job_graphs[original_job_id] = job_graph
