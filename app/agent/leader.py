import asyncio
import traceback
from typing import Dict, List, Optional, Set

import networkx as nx  # type: ignore

from app.agent.agent import Agent, AgentConfig
from app.agent.expert import Expert
from app.agent.job import Job, SubJob
from app.agent.leader_state import LeaderState
from app.common.prompt.agent import JOB_DECOMPOSITION_PROMPT
from app.common.singleton import AbcSingleton
from app.common.type import WorkflowStatus
from app.common.util import parse_json
from app.memory.message import AgentMessage, WorkflowMessage


class Leader(Agent, metaclass=AbcSingleton):
    """Leader is a role that can manage a group of agents and the jobs."""

    def __init__(self, agent_config: Optional[AgentConfig] = None, id: Optional[str] = None):
        # self._workflow of the leader is used to decompose the job

        if agent_config:
            Leader._instance_config = agent_config
        elif not Leader._instance_config:
            raise ValueError("The Leader instance config is not set.")

        super().__init__(agent_config=Leader._instance_config, id=id)
        self._leader_state: LeaderState = LeaderState()

    async def receive_submission(self, job: Job) -> None:
        """Receive a message from the user."""

        agent_message = AgentMessage(job=job)

        job_graph = await self.execute(agent_message=agent_message)

        executed_job_graph = await self.execute_job_graph(job_graph=job_graph)

        self._leader_state.replace_subgraph(
            main_job_id=job.session_id, new_subgraph=executed_job_graph
        )

    async def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> nx.DiGraph:
        """Decompose the job and execute the job.

        Args:
            agent_message (AgentMessage): The agent message including the job to be decomposed.
            retry_count (int): The number of retries.

        Returns:
            nx.DiGraph: The job graph with subjobs and dependencies.
                {
                    "job_id": {
                        "job": Job,
                        "expert_id": expert_id,
                    }
                }
        """
        # TODO: add a judgment to check if the job needs to be decomposed (to modify the prompt)

        job = agent_message.get_payload()

        # get the expert list
        expert_configs = self._leader_state.get_expert_configs()
        role_list = "\n".join(
            [
                f"Expert name: {config.profile.name}\nDescription: {config.profile.description}"
                for config in expert_configs.values()
            ]
        )

        job_decomp_prompt = JOB_DECOMPOSITION_PROMPT.format(
            num_subtasks="N (by default)",
            num_roles=3,
            task=job.goal,
            role_list=role_list,
        )
        decompsed_job = SubJob(
            session_id=job.session_id,
            goal=job.goal,
            context=job.context + f"\n\n{job_decomp_prompt}",
        )

        # decompose the job by the reasoner in the workflow
        workflow_message = await self._workflow.execute(job=decompsed_job, reasoner=self._reasoner)

        # extract the subtasks from the json block
        try:
            job_dict: Dict[str, Dict[str, str]] = parse_json(text=workflow_message.scratchpad)
            assert job_dict is not None
        except Exception as e:
            raise ValueError(
                f"Failed to decompose the subtasks by json format: {str(e)}\n"
                f"Input content:\n{workflow_message.scratchpad}"
            ) from e

        job_graph = nx.DiGraph()

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
            job_graph.add_node(
                job_id,
                job=subjob,
                expert_id=self._leader_state.get_or_create_expert_by_name(
                    subjob_dict.get("assigned_expert", "")
                ).get_id(),
            )

            # add edges for dependencies
            for dep_id in subjob_dict.get("dependencies", []):
                job_graph.add_edge(dep_id, job_id)  # dep_id -> job_id shows dependency

        if not nx.is_directed_acyclic_graph(job_graph):
            raise ValueError("The job graph is not a directed acyclic graph.")

        return job_graph

    async def execute_job_graph(self, job_graph: nx.DiGraph) -> nx.DiGraph:
        """Asynchronously execute the job graph with dependency-based parallel execution.

        Jobs are represented in a directed graph (job_graph) where edges define dependencies.
        Please make sure the job graph is a directed acyclic graph (DAG).

        Args:
            job_graph (nx.DiGraph): The job graph to be executed.

        Returns:
            nx.DiGraph: The job graph with the results of the jobs.
        """
        # TODO: move the router functionality to the experts, and make the experts be able to
        # dispatch the agent messages to the corresponding agents. The objective is to make the
        # multi-agent system more flexible, scalable, and distributed.

        pending_job_ids: Set[str] = set(job_graph.nodes())
        running_jobs: Dict[str, asyncio.Task] = {}  # job_id -> asyncio.Task
        job_results: Dict[str, WorkflowMessage] = {}  # job_id -> WorkflowMessage (result)
        job_inputs: Dict[str, AgentMessage] = {}  # job_id -> AgentMessage (input)

        while pending_job_ids:
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
                    job: Job = job_graph.nodes[job_id]["job"]
                    pred_messages: List[WorkflowMessage] = [
                        job_results[pred_id] for pred_id in job_graph.predecessors(job_id)
                    ]
                    job_inputs[job.id] = AgentMessage(job=job, workflow_messages=pred_messages)

                    ready_job_ids.add(job_id)

            # execute ready jobs
            for job_id in ready_job_ids:
                expert = self._leader_state.get_or_create_expert_by_id(
                    job_graph.nodes[job_id]["expert_id"]
                )

                running_jobs[job_id] = asyncio.create_task(
                    self._execute_job(expert, job_inputs[job_id])
                )
                pending_job_ids.remove(job_id)

            # wait for any running job to complete
            if running_jobs:
                done, _ = await asyncio.wait(
                    running_jobs.values(), return_when=asyncio.FIRST_COMPLETED
                )

                # process completed jobs
                for completed_job in done:
                    completed_job_id = next(
                        tid for tid, t in running_jobs.items() if t == completed_job
                    )
                    try:
                        agent_result: AgentMessage = await completed_job

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
                                    if pred_id in job_results:
                                        del job_results[pred_id]

                                    # update the lesson in the agent message
                                    input_agent_message = job_inputs[pred_id]
                                    lesson = agent_result.get_lesson()
                                    assert lesson is not None
                                    input_agent_message.set_lesson(lesson)
                                    job_inputs[pred_id] = input_agent_message
                        else:
                            job_results[completed_job_id] = (
                                agent_result.get_workflow_result_message()
                            )
                    except Exception as e:
                        job_results[completed_job_id] = WorkflowMessage(
                            content={
                                "status": WorkflowStatus.EXECUTION_ERROR,
                                "scratchpad": str(e) + "\n" + traceback.format_exc(),
                                "evaluation": "Some evaluation",
                            }
                        )

                    # remove from running jobs
                    del running_jobs[completed_job_id]

            # if no jobs are ready but some are pending, wait a bit
            elif pending_job_ids:
                await asyncio.sleep(0.5)

        for job_id, job_result in job_results.items():
            job_graph.nodes[job_id]["workflow_result"] = job_result
        return job_graph

    async def _execute_job(self, expert: Expert, agent_message: AgentMessage) -> AgentMessage:
        """Execute single job for the first time."""
        agent_result_message: AgentMessage = await expert.execute(agent_message=agent_message)
        workflow_result: WorkflowMessage = agent_result_message.get_workflow_result_message()

        if workflow_result.status == WorkflowStatus.SUCCESS:
            return agent_result_message
        elif workflow_result.status == WorkflowStatus.INPUT_DATA_ERROR:
            # reexecute all the dependent jobs (predecessors)
            return agent_result_message
        elif workflow_result.status == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR:
            # TODO: implement the decompose job method
            # job_graph, expert_assignments = await self._decompse_job(
            #     job=job, num_subjobs=2
            # )
            raise NotImplementedError("Decompose the job into subjobs is not implemented.")
        raise ValueError(f"Unexpected workflow status: {workflow_result.status}")

    def get_leader_state(self) -> LeaderState:
        """Get the leader state."""
        return self._leader_state
