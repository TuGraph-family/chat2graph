import threading
from typing import Dict, List, Optional

import networkx as nx  # type: ignore

from app.agent.agent import AgentConfig
from app.agent.expert import Expert
from app.agent.job import Job
from app.common.util import Singleton


class LeaderState(metaclass=Singleton):
    """Leader State is uesd to manage expert agent and jobs.

    attributes:
        _job_graph: the oriented graph of the jobs.
        _expert_assignments: the expert dictionary (Job_id -> expert).

        Jobs schema
            {
                "job_id": {
                    "job": job,
                    "expert_id": expert_id,
                    "workflow_result": workflow_message,
                }
            }
    """

    def __init__(self):
        # Store class and config information, not instances
        self._job_graphs: Dict[str, nx.DiGraph] = {}  # session_id -> nx.DiGraph
        self._expert_configs: Dict[str, AgentConfig] = {}  # name -> agent_config
        self._expert_instances: Dict[str, Expert] = {}  # expert_id -> expert

        # TODO: if we define the lock for every expert, we can avoid some the lock contentions
        self._expert_creation_lock: threading.Lock = threading.Lock()

    def get_or_create_expert_by_name(self, expert_name: str) -> Expert:
        """Get existing expert instance or create a new one."""
        # get expert ID by expert name
        if expert_name not in self._expert_configs:
            raise ValueError(f"Expert config with name {expert_name} not found")
        expert_id = self._expert_configs[expert_name].profile.name

        # get expert instance by expert ID
        with self._expert_creation_lock:
            if expert_id not in self._expert_instances:
                expert = Expert(agent_config=self._expert_configs[expert_name])
                expert_id = expert.get_id()
                self._expert_instances[expert_id] = expert
                return expert
            return self._expert_instances[expert_id]

    def get_or_create_expert_by_id(self, expert_id: str) -> Expert:
        """Get existing expert instance or create a new one."""
        # get expert instance by expert ID
        with self._expert_creation_lock:
            if expert_id not in self._expert_instances:
                raise ValueError(f"Expert with ID {expert_id} not found in the expert registry.")
            return self._expert_instances[expert_id]

    def release_expert(self, expert_id: str) -> None:
        """Release the expert"""
        # TODO: implement expert release
        raise NotImplementedError("Expert release is not implemented.")

    def list_experts(self) -> List[Expert]:
        """Return a list of all registered expert information."""
        # TODO: implement expert list
        raise NotImplementedError("Expert list is not implemented.")

    def add_job(
        self,
        job: Job,
        expert_name: str,
        predecessors: Optional[List[Job]] = None,
        successors: Optional[List[Job]] = None,
    ) -> Expert:
        """Assign a job to an expert and return the expert instance."""
        expert = self.get_or_create_expert_by_name(expert_name)

        # add job to the jobs graph
        job_graph = self.get_job_graph(job.session_id)
        job_graph.add_node(job.id, job=job, expert_id=expert.get_id())

        if not predecessors:
            predecessors = []
        if not successors:
            successors = []
        for predecessor in predecessors:
            job_graph.add_edge(predecessor.id, job.id)
        for successor in successors:
            job_graph.add_edge(job.id, successor.id)

        self._job_graphs[job.session_id] = job_graph

        return expert

    def remove_job(self, session_id: str, job_id: str) -> None:
        """Remove a Job from the Job registry."""
        job_graph = self.get_job_graph(session_id)
        job_graph.remove_node(job_id)
        self._job_graphs[session_id] = job_graph

    def get_job(self, session_id: str, job_id: str) -> Job:
        """Get a Job from the Job registry."""
        return self.get_job_graph(session_id).nodes[job_id]["job"]

    def get_expert_by_job_id(self, session_id: str, job_id: str) -> Expert:
        """Get an expert from the expert registry."""
        return self.get_or_create_expert_by_id(
            self.get_job_graph(session_id).nodes[job_id]["expert_id"]
        )

    def get_job_graph(self, session_id: str) -> nx.DiGraph:
        """Get the Jobs graph."""
        if session_id not in self._job_graphs:
            self._job_graphs[session_id] = nx.DiGraph()
        return self._job_graphs[session_id]

    def add_expert_config(self, expert_name: str, agent_config: AgentConfig) -> None:
        """Add an expert profile to the registry."""
        self._expert_configs[expert_name] = agent_config

    def remove_expert_config(self, expert_name: str) -> None:
        """Remove an expert profile from the registry."""
        del self._expert_configs[expert_name]

    def get_expert_config(self, expert_name: str) -> AgentConfig:
        """Get an expert profile from the registry."""
        return self._expert_configs[expert_name]

    def get_expert_configs(self) -> Dict[str, AgentConfig]:
        """Return a dictionary of all registered expert profiles."""
        return dict(self._expert_configs)

    def replace_subgraph(
        self,
        session_id: str,
        new_subgraph: nx.DiGraph,
        old_subgraph: Optional[nx.DiGraph] = None,
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
            session_id (str): The session ID of the jobs DAG to update.
            new_subgraph (nx.DiGraph): The new subgraph to insert. Must have all nodes containing
                'job' and 'expert_id' attributes.
            old_subgraph (Optional[nx.DiGraph]): The subgraph to be replaced. Must be a connected
                component of the current jobs DAG with exactly one entry and one exit node.
        """
        # validate
        for node, data in new_subgraph.nodes(data=True):
            if "job" not in data or not isinstance(data["job"], Job):
                raise ValueError(f"Node {node} missing required 'job' attribute")
            if "expert_id" not in data:
                raise ValueError(f"Node {node} missing required 'expert_id' attribute")

        job_graph = self.get_job_graph(session_id)

        if old_subgraph is None:
            job_graph.update(new_subgraph)
            return

        old_subgraph_nodes = set(old_subgraph.nodes())
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
        _topological_sorted_nodes = list(nx.topological_sort(new_subgraph))
        head_node = _topological_sorted_nodes[0]
        tail_node = _topological_sorted_nodes[-1]
        for predecessor in predecessors:
            job_graph.add_edge(predecessor, head_node)
        for successor in successors:
            job_graph.add_edge(tail_node, successor)

        self._job_graphs[session_id] = job_graph
