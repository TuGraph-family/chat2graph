import time
from typing import List, Optional, Set, cast

import networkx as nx  # type: ignore

from app.core.common.singleton import Singleton
from app.core.common.type import ChatMessageRole, JobStatus
from app.core.dal.dao.job_dao import JobDao
from app.core.dal.do.job_do import JobDo
from app.core.model.job import Job, JobType, SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.job_result import JobResult
from app.core.model.message import AgentMessage, MessageType, TextMessage
from app.core.service.message_service import MessageService


class JobService(metaclass=Singleton):
    """Job service"""

    def __init__(self):
        self._job_dao: JobDao = JobDao.instance

    def save_job(self, job: Job) -> Job:
        """Save a new job."""
        self._job_dao.save_job(job=job)
        return job

    def get_original_job_ids(self) -> List[str]:
        """Get all job ids."""
        return [str(job_do.id) for job_do in self._job_dao.filter_by(category=JobType.JOB.value)]

    def get_orignal_job(self, original_job_id: str) -> Job:
        """Get a job from the job registry."""
        return self._job_dao.get_job_by_id(original_job_id)

    def get_original_jobs_by_session_id(self, session_id: str) -> List[Job]:
        """Get all original jobs by session id."""
        results = self._job_dao.filter_by(session_id=session_id, category=JobType.JOB.value)
        jobs: List[Job] = []
        for result in results:
            jobs.append(
                Job(
                    id=str(result.id),
                    session_id=str(result.session_id),
                    goal=str(result.goal),
                    context=str(result.context),
                    assigned_expert_name=cast(Optional[str], result.assigned_expert_name),
                    dag=cast(Optional[str], result.dag),
                )
            )
        return jobs

    def get_subjob_ids(self, original_job_id: str) -> List[str]:
        """Get all subjob ids."""
        # return self.get_job_graph(original_job_id).vertices()  # it is too wasteful
        return [
            str(job_do.id) for job_do in self._job_dao.filter_by(original_job_id=original_job_id)
        ]

    def get_subjobs(self, original_job_id: Optional[str] = None) -> List[SubJob]:
        """Get all subjobs."""
        if original_job_id:
            return [self.get_subjob(job_id) for job_id in self.get_subjob_ids(original_job_id)]

        # get all subjobs from all job graphs
        subjobs: List[SubJob] = []
        for original_id in self.get_original_job_ids():
            subjobs.extend(self.get_subjobs(original_id))
        return subjobs

    def get_subjob(self, subjob_id: str) -> SubJob:
        """Get a Job from the job registry."""
        return cast(SubJob, self._job_dao.get_job_by_id(subjob_id))

    def get_job_result(self, job_id: str) -> JobResult:
        """return the job result by job id."""
        job_do: Optional[JobDo] = self._job_dao.get_by_id(id=job_id)
        if not job_do:
            raise ValueError(f"Job with id {job_id} not found in the job registry.")
        return JobResult(
            job_id=job_id,
            status=JobStatus[str(job_do.status)],
            duration=float(job_do.duration),
            tokens=int(job_do.tokens),
        )

    def save_job_result(self, job_result: JobResult) -> None:
        """Update the job result."""
        self._job_dao.save_job_result(job_result=job_result)

    def query_job_result(self, job_id: str) -> JobResult:
        """Query the result of the multi-agent system by original job id."""
        message_service: MessageService = MessageService.instance

        # check if the original job already has gotten the job result
        job_result: JobResult = self.get_job_result(job_id)
        if job_result.has_result():
            return job_result

        # get the tail vertices of the job graph (DAG)
        tail_vertices: List[str] = []
        while len(tail_vertices) == 0:
            # wait for creating the subjob by leader
            job_graph = self.get_job_graph(job_id)
            tail_vertices = [
                vertex for vertex in job_graph.vertices() if job_graph.out_degree(vertex) == 0
            ]
            time.sleep(1)

        # collect and combine the content of the job results from the tail vertices
        mutli_agent_payload = ""
        for tail_vertex in tail_vertices:
            subjob_result: JobResult = self.get_job_result(tail_vertex)
            if not subjob_result.has_result():
                # not all the subjobs have been finished, so return the job result itself
                self.save_job_result(job_result=job_result)
                return job_result
            if job_result.status == JobStatus.CREATED:
                # if at least one subjob is finished, and the original job is created,
                # now the original job is running
                job_result.status = JobStatus.RUNNING

            agent_messages: List[AgentMessage] = cast(
                List[AgentMessage],
                message_service.get_message_by_job_id(
                    job_id=subjob_result.job_id, message_type=MessageType.AGENT_MESSAGE
                ),
            )
            assert len(agent_messages) == 1, (
                f"One subjob is assigned to one agent, but {len(agent_messages)} messages found."
            )
            assert agent_messages[0].get_payload() is not None, (
                "The agent message payload is empty."
            )
            mutli_agent_payload += cast(str, agent_messages[0].get_payload()) + "\n"

        # save the multi-agent result to the database
        original_job: Job = self.get_orignal_job(job_id)
        try:
            multi_agent_message = message_service.get_text_message_by_job_id_and_role(
                job_id, ChatMessageRole.SYSTEM
            )
            multi_agent_message.set_payload(mutli_agent_payload)
        except ValueError:
            multi_agent_message = TextMessage(
                payload=mutli_agent_payload,
                job_id=job_id,
                session_id=original_job.session_id,
                assigned_expert_name=original_job.assigned_expert_name,
                role=ChatMessageRole.SYSTEM,
            )
        message_service.save_message(message=multi_agent_message)

        # save the original job result
        job_result.status = JobStatus.FINISHED
        self.save_job_result(job_result=job_result)
        return job_result

    def get_job_graph(self, job_id: str) -> JobGraph:
        """Get the job graph by the inital job id. If the job graph does not exist,
        create a new one and save it to the database."""
        job_do = self._job_dao.get_by_id(job_id)
        if not job_do:
            raise ValueError(f"Job with ID {job_id} not found in the job registry")

        if not job_do.dag:
            job_graph: JobGraph = JobGraph()
            self._job_dao.update(id=job_id, dag=job_graph.to_json_str())
        else:
            job_graph = JobGraph.from_json_str(str(job_do.dag))
        return job_graph

    def set_job_graph(self, job_id: str, job_graph: JobGraph) -> None:
        """Set the job graph by the inital job id."""
        # save the jobs to the databases
        original_job: Job = self.get_orignal_job(job_id)
        original_job.dag = job_graph.to_json_str()
        self.save_job(original_job)
        for subjob_id in job_graph.vertices():
            self.save_job(job=self.get_subjob(subjob_id))

    def add_job(
        self,
        original_job_id: str,
        job: SubJob,
        expert_id: str,
        predecessors: Optional[List[SubJob]] = None,
        successors: Optional[List[SubJob]] = None,
    ) -> None:
        """Assign a job to an expert and return the expert instance."""
        # add job to the jobs graph
        job_graph = self.get_job_graph(original_job_id)
        job_graph.add_vertex(job.id)

        job.original_job_id = original_job_id
        job.expert_id = expert_id

        # save the job to the database
        self.save_job(job=job)

        if not predecessors:
            predecessors = []
        if not successors:
            successors = []
        for predecessor in predecessors:
            job_graph.add_edge(predecessor.id, job.id)
            self.save_job(predecessor)
        for successor in successors:
            self.save_job(successor)
            job_graph.add_edge(job.id, successor.id)

        self.set_job_graph(original_job_id, job_graph)

    def remove_job(self, original_job_id: str, job_id: str) -> None:
        """Remove a job from the job registry."""
        # remove the job from the database
        # and mark the job as a legacy job
        subjob = self.get_subjob(job_id)
        subjob.is_legacy = True
        self.save_job(subjob)

        # update the state of the job service
        job_graph = self.get_job_graph(original_job_id)
        job_graph.remove_vertex(job_id)
        self.set_job_graph(job_id=original_job_id, job_graph=job_graph)

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
        job_graph: JobGraph = self.get_job_graph(original_job_id)

        if not old_subgraph:
            job_graph.update(new_subgraph)

            # save the updated jobs to the database
            self.set_job_graph(original_job_id, job_graph)
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
        for vertex in old_subgraph_vertices:
            job = self.get_subjob(vertex)
            job.is_legacy = True
            self._job_dao.save_job(job=job)

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

        # save the updated jobs to the database
        self.set_job_graph(original_job_id, job_graph)
