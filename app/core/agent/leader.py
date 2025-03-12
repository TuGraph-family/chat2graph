from concurrent.futures import Future, ThreadPoolExecutor
import time
import traceback
from typing import Dict, List, Optional, Set

import networkx as nx  # type: ignore

from app.core.agent.agent import Agent, AgentConfig
from app.core.agent.builtin_leader_state import BuiltinLeaderState
from app.core.agent.expert import Expert
from app.core.agent.leader_state import LeaderState
from app.core.common.type import JobStatus, WorkflowStatus
from app.core.common.util import parse_json
from app.core.model.job import Job, SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.job_result import JobResult
from app.core.model.message import AgentMessage, TextMessage, WorkflowMessage
from app.core.prompt.agent import JOB_DECOMPOSITION_PROMPT
from app.core.service.job_service import JobService


class Leader(Agent):
    """Leader is a role that can manage a group of agents and the jobs."""

    def __init__(
        self,
        agent_config: AgentConfig,
        id: Optional[str] = None,
        leader_state: Optional[LeaderState] = None,
    ):
        super().__init__(agent_config=agent_config, id=id)
        # self._workflow of the leader is used to decompose the job
        self._leader_state: LeaderState = leader_state or BuiltinLeaderState()
        self._job_service: JobService = JobService.instance

    def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> JobGraph:
        """Decompose the job into subjobs.

        Args:
            agent_message (AgentMessage): The agent message including the job to be decomposed.
            retry_count (int): The number of retries.

        Returns:
            JobGraph: The job graph of the subjobs.
        """
        # TODO: add a judgment to check if the job needs to be decomposed (to modify the prompt)

        job_id = agent_message.get_job_id()
        try:
            job: Job = self._job_service.get_orignal_job(original_job_id=job_id)
        except ValueError:
            job = self._job_service.get_subjob(job_id=job_id)

        # check if the job is already assigned to an expert
        assigned_expert_name: Optional[str] = job.assigned_expert_name
        if assigned_expert_name:
            expert = self.state.get_expert_by_name(assigned_expert_name)
            job_graph: JobGraph = JobGraph()
            job_graph.add_vertex(
                job.id,
                job=SubJob(
                    id=job.id,
                    session_id=job.session_id,
                    goal=job.goal,
                    context=job.goal + "\n" + job.context,
                ),
                expert_id=expert.get_id(),
            )
            return job_graph

        # else, the job is not assigned to an expert, then decompose the job
        # get the expert list
        expert_profiles = [e.get_profile() for e in self.state.list_experts()]
        role_list = "\n".join(
            [
                f"Expert name: {profile.name}\nDescription: {profile.description}"
                for profile in expert_profiles
            ]
        )

        job_decomp_prompt = JOB_DECOMPOSITION_PROMPT.format(task=job.goal, role_list=role_list)
        decompsed_job = SubJob(
            session_id=job.session_id,
            goal=job.goal,
            context=job.context + f"\n\n{job_decomp_prompt}",
        )

        # decompose the job by the reasoner in the workflow
        workflow_message = self._workflow.execute(job=decompsed_job, reasoner=self._reasoner)

        # extract the subjobs from the json block
        try:
            job_dict: Dict[str, Dict[str, str]] = parse_json(text=workflow_message.scratchpad)
            assert job_dict is not None
        except Exception as e:
            raise ValueError(
                f"Failed to decompose the subjobs by json format: {str(e)}\n"
                f"Input content:\n{workflow_message.scratchpad}"
            ) from e

        # init the decomposed job graph
        job_graph = JobGraph()

        # create the subjobs, and add them to the decomposed job graph
        for job_id, subjob_dict in job_dict.items():
            subjob = SubJob(
                id=job_id,
                session_id=job.session_id,
                goal=subjob_dict.get("goal", ""),
                context=(
                    subjob_dict.get("context", "")
                    + "\n"
                    + subjob_dict.get("completion_criteria", "")
                ),
            )
            # add the subjob to the job graph
            job_graph.add_vertex(
                job_id,
                job=subjob,
                expert_id=self.state.get_expert_by_name(
                    subjob_dict.get("assigned_expert", "")
                ).get_id(),
            )

            # add edges for dependencies
            for dep_id in subjob_dict.get("dependencies", []):
                job_graph.add_edge(dep_id, job_id)  # dep_id -> job_id shows dependency

        # the job graph should not be a directed acyclic graph (DAG)
        if not nx.is_directed_acyclic_graph(job_graph.get_graph()):
            raise ValueError("The job graph is not a directed acyclic graph.")

        return job_graph

    def execute_job(self, job: Job) -> None:
        """Execute the job."""
        # decompose the job into decomposed job graph
        decomposed_job_graph: JobGraph = self.execute(agent_message=AgentMessage(job_id=job.id))

        # update the decomposed job graph in the job service
        self._job_service.replace_subgraph(
            original_job_id=job.id, new_subgraph=decomposed_job_graph
        )

        # execute the decomposed job graph
        self.execute_job_graph(original_job_id=job.id)

    def execute_job_graph(self, original_job_id: str) -> None:
        """Execute the job graph with dependency-based parallel execution.

        Jobs are represented in a directed graph (job_graph) where edges define dependencies.
        Please make sure the job graph is a directed acyclic graph (DAG).

        Args:
            original_job_id (str): The original job id.
        """
        # TODO: move the router functionality to the experts, and make the experts be able to
        # dispatch the agent messages to the corresponding agents. The objective is to make the
        # multi-agent system more flexible, scalable, and distributed.

        job_graph: JobGraph = self._job_service.get_job_graph(original_job_id)
        pending_job_ids: Set[str] = set(job_graph.vertices())
        running_jobs: Dict[str, Future] = {}  # job_id -> Concurrent Future
        expert_results: Dict[str, WorkflowMessage] = {}  # job_id -> WorkflowMessage (expert result)
        job_inputs: Dict[str, AgentMessage] = {}  # job_id -> AgentMessage (input)

        with ThreadPoolExecutor() as executor:
            while pending_job_ids or running_jobs:
                # find jobs that are ready to execute (all dependencies completed)
                ready_job_ids: Set[str] = set()
                for job_id in pending_job_ids:
                    # check if all predecessors are completed
                    all_predecessors_completed = all(
                        pred not in pending_job_ids and pred not in running_jobs
                        for pred in job_graph.predecessors(job_id)
                    )
                    if all_predecessors_completed:
                        # form the agent message to the agent
                        job: Job = job_graph.get_job(job_id)
                        pred_messages: List[WorkflowMessage] = [
                            expert_results[pred_id] for pred_id in job_graph.predecessors(job_id)
                        ]
                        job_inputs[job.id] = AgentMessage(
                            job_id=job.id, workflow_messages=pred_messages
                        )
                        ready_job_ids.add(job_id)

                # execute ready jobs
                for job_id in ready_job_ids:
                    expert = self.state.get_expert_by_id(job_graph.get_expert_id(job_id))
                    # submit the job to the executor
                    running_jobs[job_id] = executor.submit(
                        self._execute_job, expert, job_inputs[job_id]
                    )
                    pending_job_ids.remove(job_id)

                # if there are no running jobs but still pending jobs, it may be a deadlock
                if not running_jobs and pending_job_ids:
                    raise ValueError(
                        "Deadlock detected or invalid job graph: some jobs cannot be executed due to dependencies."
                    )

                # check for completed jobs
                completed_job_ids = []
                for job_id, future in running_jobs.items():
                    if future.done():
                        completed_job_ids.append(job_id)

                # process completed jobs
                for completed_job_id in completed_job_ids:
                    future = running_jobs[completed_job_id]
                    try:
                        # get the agent result
                        agent_result: AgentMessage = future.result()

                        if (
                            agent_result.get_workflow_result_message().status
                            == WorkflowStatus.INPUT_DATA_ERROR
                        ):
                            pending_job_ids.add(completed_job_id)
                            predecessors = list(job_graph.predecessors(completed_job_id))

                            # add the predecessors back to pending jobs
                            pending_job_ids.update(predecessors)

                            if predecessors:
                                for pred_id in predecessors:
                                    # remove the job result
                                    if pred_id in expert_results:
                                        del expert_results[pred_id]
                                        # update the result in the job service
                                        self._job_service.get_job_graph(
                                            original_job_id
                                        ).remmove_job_result(id=pred_id)

                                    # update the lesson in the agent message
                                    input_agent_message = job_inputs[pred_id]
                                    lesson = agent_result.get_lesson()
                                    assert lesson is not None
                                    input_agent_message.set_lesson(lesson)
                                    job_inputs[pred_id] = input_agent_message
                        else:
                            expert_results[completed_job_id] = (
                                agent_result.get_workflow_result_message()
                            )
                            # update the result in the job service
                            self._job_service.get_job_graph(original_job_id).set_job_result(
                                completed_job_id,
                                JobResult(
                                    job_id=completed_job_id,
                                    status=JobStatus.FINISHED,
                                    result=TextMessage(
                                        payload=agent_result.get_workflow_result_message().scratchpad,
                                        job_id=completed_job_id,
                                    ),
                                ),
                            )
                    except Exception as e:
                        expert_results[completed_job_id] = WorkflowMessage(
                            payload={
                                "status": WorkflowStatus.EXECUTION_ERROR,
                                "scratchpad": str(e) + "\n" + traceback.format_exc(),
                                "evaluation": "Some evaluation",
                            },
                            job_id=completed_job_id,
                        )
                        # update the result in the job service
                        self._job_service.get_job_graph(original_job_id).set_job_result(
                            completed_job_id,
                            JobResult(
                                job_id=completed_job_id,
                                status=JobStatus.FAILED,
                                result=TextMessage(
                                    payload=str(e) + "\n" + traceback.format_exc(),
                                    job_id=completed_job_id,
                                ),
                            ),
                        )

                    # remove from running jobs
                    del running_jobs[completed_job_id]

                # if no jobs are ready but some are pending, wait a bit
                if not completed_job_ids and running_jobs:
                    time.sleep(0.5)

    def _execute_job(self, expert: Expert, agent_message: AgentMessage) -> AgentMessage:
        """Dispatch the job to the expert, and handle the result."""
        agent_result_message: AgentMessage = expert.execute(agent_message=agent_message)
        workflow_result: WorkflowMessage = agent_result_message.get_workflow_result_message()

        if workflow_result.status == WorkflowStatus.SUCCESS:
            return agent_result_message
        elif workflow_result.status == WorkflowStatus.INPUT_DATA_ERROR:
            # reexecute all the dependent jobs (predecessors)
            return agent_result_message
        elif workflow_result.status == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR:
            # TODO: implement the decompose job method
            # job_graph, expert_assignments = self._decompse_job(
            #     job=job, num_subjobs=2
            # )
            raise NotImplementedError("Decompose the job into subjobs is not implemented.")
        raise ValueError(f"Unexpected workflow status: {workflow_result.status}")

    @property
    def state(self) -> LeaderState:
        """Get the leader state."""
        return self._leader_state
