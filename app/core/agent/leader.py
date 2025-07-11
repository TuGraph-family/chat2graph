from concurrent.futures import Future, ThreadPoolExecutor
import json
import time
from typing import Dict, List, Optional, Set, Union

import networkx as nx  # type: ignore

from app.core.agent.agent import Agent, AgentConfig
from app.core.agent.builtin_leader_state import BuiltinLeaderState
from app.core.agent.expert import Expert
from app.core.agent.leader_state import LeaderState
from app.core.common.async_func import run_in_thread
from app.core.common.system_env import SystemEnv
from app.core.common.type import ChatMessageRole, JobStatus, WorkflowStatus
from app.core.common.util import parse_jsons
from app.core.model.job import Job, SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.message import AgentMessage, HybridMessage, TextMessage, WorkflowMessage
from app.core.prompt.job_decomposition import (
    JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    TASK_AND_PROFILE_PROMPT,
    subjob_required_keys,
)


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

    def execute(self, agent_message: AgentMessage, retry_count: int = 0) -> JobGraph:
        """Decompose the original job into subjobs.

        Args:
            agent_message (AgentMessage): The agent message including the job to be decomposed.
            retry_count (int): The number of retries.

        Returns:
            JobGraph: The job graph of the subjobs.
        """
        life_cycle: Optional[int] = None
        job_id = agent_message.get_job_id()
        try:
            job: Job = self._job_service.get_original_job(original_job_id=job_id)
            original_job_id: str = job_id
        except ValueError as e:
            job = self._job_service.get_subjob(subjob_id=job_id)
            life_cycle = job.life_cycle
            if not job.original_job_id:
                raise ValueError("The subjob is not assigned to an original job.") from e
            original_job_id = job.original_job_id

        # check if the job is already assigned to an expert
        assigned_expert_name: Optional[str] = job.assigned_expert_name
        if assigned_expert_name:
            expert = self.state.get_expert_by_name(assigned_expert_name)
            subjob = SubJob(
                original_job_id=original_job_id,
                session_id=job.session_id,
                goal=job.goal,
                context=job.goal + "\n" + job.context,
                expert_id=expert.get_id(),
                life_cycle=life_cycle or SystemEnv.LIFE_CYCLE,
                assigned_expert_name=assigned_expert_name,
            )
            self._job_service.save_job(job=subjob)
            job_graph: JobGraph = JobGraph()
            job_graph.add_vertex(subjob.id)
            return job_graph

        # else, the job is not assigned to an expert, then decompose the job
        # get the expert list
        expert_profiles = [e.get_profile() for e in self.state.list_experts()]
        expert_names = [p.name for p in expert_profiles]  # get list of names for validation
        role_list = "\n".join(
            [
                f"Expert name: {profile.name}\nDescription: {profile.description}"
                for profile in expert_profiles
            ]
        )

        job_decomp_prompt = TASK_AND_PROFILE_PROMPT.format(task=job.goal, role_list=role_list)
        decomp_job = Job(
            id=job.id,
            session_id=job.session_id,
            goal=job.goal,
            context=job.context + f"\n\n{job_decomp_prompt}",
        )

        job_dict: Optional[Dict[str, Dict[str, str]]] = None

        try:
            # decompose the job by the reasoner in the workflow
            workflow_message = self._workflow.execute(job=decomp_job, reasoner=self._reasoner)

            # extract the subjobs from the json block
            results: List[Union[Dict[str, Dict[str, str]], json.JSONDecodeError]] = parse_jsons(
                text=workflow_message.scratchpad,
                start_marker=r"^\s*<decomposition>\s*",
                end_marker="</decomposition>",
            )

            if len(results) == 0:
                raise ValueError("The job decomposition result is empty.")
            result = results[0]

            # if parse_jsons returns a JSONDecodeError directly, raise it
            if isinstance(result, json.JSONDecodeError):
                raise result

            # validate the parsed dictionary
            self._validate_job_dict(result, expert_names)
            job_dict = result

        except (ValueError, json.JSONDecodeError, Exception) as e:
            # color: red
            print(
                f"\033[38;5;196m[WARNING]: Initial decomposition failed or validation error: "
                f"{e}\033[0m"
            )

            # check if it's a validation/parsing error eligible for retry
            if isinstance(e, ValueError | json.JSONDecodeError):
                # retry to decompose the job with the new lesson
                # color: orange
                print("\033[38;5;208m[INFO]: Retrying decomposition with lesson...\033[0m")
                lesson = (
                    "LLM output format (<decomposition> format) specification is crucial "
                    "for reliable parsing and validation. Ensure the JSON structure is correct, "
                    f"all required keys are present: {subjob_required_keys}, dependencies are "
                    f"valid task IDs, and assigned_expert is one of {expert_names}. Do not forget "
                    " <decomposition> prefix and </decomposition> suffix when you generate the "
                    "subtasks dict block in <final_output>...</final_output>.\nExpected format: "
                    f"{JOB_DECOMPOSITION_OUTPUT_SCHEMA}\nError info: " + str(e)
                )
                try:
                    workflow_message = self._workflow.execute(
                        job=decomp_job,
                        reasoner=self._reasoner,
                        lesson=lesson,
                    )
                    # extract the subjobs from the json block after retry
                    results = parse_jsons(
                        text=workflow_message.scratchpad,
                        start_marker=r"^\s*<decomposition>\s*",
                        end_marker="</decomposition>",
                    )
                    if len(results) == 0:
                        raise ValueError(
                            "The job decomposition result is empty after retry."
                        ) from e
                    result = results[0]
                    # if parse_jsons returns a JSONDecodeError directly, raise it
                    if isinstance(result, json.JSONDecodeError):
                        raise result from e

                    # validate the parsed dictionary after retry
                    self._validate_job_dict(result, expert_names)
                    job_dict = result

                except (ValueError, json.JSONDecodeError) as retry_e:
                    self.fail_job_graph(
                        job_id=job_id,
                        error_info=(
                            f"The job `{original_job_id}` could not be decomposed correctly "
                            f"after retry. Please try again.\nError info: {retry_e}"
                        ),
                    )
                    job_dict = {}
            else:
                # handle non-retryable exceptions (e.g., network errors during _workflow.execute)
                # stop the job graph
                self.fail_job_graph(
                    job_id=job_id,
                    error_info=(
                        f"The job `{original_job_id}` could not be executed due to an "
                        f"unexpected error during leader task decomposition. Error info: {e}"
                    ),
                )
                job_dict = {}

        # if decomposition failed and wasn't retried or retry failed, job_dict might be {}
        if not job_dict:  # check if job_dict is empty or None
            # ensure the job status reflects failure if not already set by fail_job_graph
            current_status = self._job_service.get_job_result(job_id=job_id).status
            if current_status not in (JobStatus.FAILED, JobStatus.STOPPED):
                # use a generic error message if specific one wasn't set in except blocks
                self.fail_job_graph(
                    job_id,
                    "Decomposition failed to produce a valid and non-empty subtask dictionary.",
                )
            return JobGraph()

        # initialize the job graph
        job_graph = JobGraph()

        # check the current job (original job / subjob) status
        if self._job_service.get_job_result(job_id=job_id).has_result():
            return job_graph

        # create the subjobs, and add them to the decomposed job graph
        temp_to_unique_id_map: Dict[str, str] = {}  # id_generated_by_leader -> unique_id
        try:
            # this loop assumes job_dict was validated successfully above
            for subjob_id, subjob_dict in job_dict.items():
                expert_name = subjob_dict["assigned_expert"]
                expert = self.state.get_expert_by_name(
                    expert_name
                )  # Should succeed if validation passed
                subjob = SubJob(
                    original_job_id=original_job_id,
                    session_id=job.session_id,
                    goal=subjob_dict["goal"],
                    context=(
                        subjob_dict["context"]
                        + "\nThe completion criteria is determined: "
                        + subjob_dict["completion_criteria"]
                    ),
                    expert_id=expert.get_id(),
                    life_cycle=life_cycle or SystemEnv.LIFE_CYCLE,
                    thinking=subjob_dict["thinking"],
                    assigned_expert_name=expert_name,
                )
                temp_to_unique_id_map[subjob_id] = subjob.id

                self._job_service.save_job(job=subjob)
                # add the subjob to the job graph
                job_graph.add_vertex(subjob.id)

            for subjob_id, subjob_dict in job_dict.items():
                # add edges for dependencies (already validated)
                current_unique_id = temp_to_unique_id_map[subjob_id]
                for dep_id in subjob_dict.get(
                    "dependencies", []
                ):  # use .get for safety, though validated
                    dep_unique_id = temp_to_unique_id_map[dep_id]  # Already validated to exist
                    job_graph.add_edge(
                        dep_unique_id, current_unique_id
                    )  # dep_id -> subjob_id shows dependency
        except Exception as e:  # catch unexpected errors during subjob creation/linking
            # although validation passed, errors might occur during DB interaction or expert lookup
            self.fail_job_graph(
                job_id=job_id,
                error_info=(
                    f"The job `{original_job_id}` decomposition was validated, but an error "
                    f"occurred during subjob creation or linking.\nError info: {e}"
                ),
            )
            return JobGraph()

        # the job graph should be a directed acyclic graph (DAG)
        if not nx.is_directed_acyclic_graph(job_graph.get_graph()):
            self.fail_job_graph(
                job_id=job_id,
                error_info=(
                    f"The job `{original_job_id}` decomposition resulted in a cyclic graph, "
                    f"indicating an issue with dependency logic despite validation."
                ),
            )
            return JobGraph()

        return job_graph

    def execute_original_job(self, original_job: Job) -> None:
        """Execute the job."""
        # update the job status to running
        original_job_result = self._job_service.get_job_result(job_id=original_job.id)
        if original_job_result.status == JobStatus.CREATED:
            original_job_result.status = JobStatus.RUNNING
            self._job_service.save_job_result(job_result=original_job_result)
        else:
            # note: if the job status is running, it means the leader will generate at least two
            # job graphs, which may lead to the leakage of the subjobs
            raise ValueError(
                f"Original job {original_job.id} already has a final or running status: "
                f"{original_job_result.status.value}."
            )

        # decompose the job into decomposed job graph
        decomposed_job_graph: JobGraph = self.execute(
            agent_message=AgentMessage(
                job_id=original_job.id,
            )
        )

        # update the decomposed job graph in the job service
        self._job_service.replace_subgraph(
            original_job_id=original_job.id, new_subgraph=decomposed_job_graph
        )

        # execute the decomposed job graph
        self.execute_job_graph(original_job_id=original_job.id)

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
                        job: SubJob = self._job_service.get_subjob(job_id)
                        pred_messages: List[WorkflowMessage] = [
                            expert_results[pred_id] for pred_id in job_graph.predecessors(job_id)
                        ]
                        job_inputs[job.id] = AgentMessage(
                            job_id=job.id, workflow_messages=pred_messages
                        )
                        ready_job_ids.add(job_id)

                # execute ready jobs
                for job_id in ready_job_ids:
                    expert_id = self._job_service.get_subjob(job_id).expert_id
                    assert expert_id, "The subjob is not assigned to an expert."
                    expert = self.state.get_expert_by_id(expert_id=expert_id)
                    # submit the job to the executor
                    running_jobs[job_id] = executor.submit(
                        self._execute_job, expert, job_inputs[job_id]
                    )
                    pending_job_ids.remove(job_id)

                # if there are no running jobs but still pending jobs, it may be a deadlock
                if not running_jobs and pending_job_ids:
                    raise ValueError(
                        "Deadlock detected or invalid job graph: some jobs cannot be executed due "
                        "to dependencies."
                    )

                # check for completed jobs
                completed_job_ids = []
                for job_id, future in running_jobs.items():
                    if future.done():
                        completed_job_ids.append(job_id)

                # process completed jobs
                for completed_job_id in completed_job_ids:
                    future = running_jobs[completed_job_id]

                    # get the agent result
                    agent_result: AgentMessage = future.result()

                    if (
                        agent_result.get_workflow_result_message().status
                        == WorkflowStatus.INPUT_DATA_ERROR
                    ):
                        # TODO: how to handle the concurrent situations?
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
                                    self._job_service.remove_subjob(
                                        original_job_id=original_job_id, job_id=pred_id
                                    )

                                # update the lesson in the agent message
                                input_agent_message = job_inputs[pred_id]
                                lesson = agent_result.get_lesson()
                                assert lesson is not None
                                input_agent_message.add_lesson(lesson)
                                job_inputs[pred_id] = input_agent_message

                    elif (
                        agent_result.get_workflow_result_message().status
                        == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR
                    ):
                        # TODO: how to handle the concurrent situations?
                        old_job_graph: JobGraph = JobGraph()
                        old_job_graph.add_vertex(completed_job_id)

                        # reexecute the subjob with a new sub-subjob
                        new_job_graqph: JobGraph = self.execute(agent_message=agent_result)
                        self._job_service.replace_subgraph(
                            original_job_id=original_job_id,
                            new_subgraph=new_job_graqph,
                            old_subgraph=old_job_graph,
                        )

                        # get the newest job graph
                        job_graph = self._job_service.get_job_graph(original_job_id)

                        # remove the old subjob from the pending jobs
                        del running_jobs[completed_job_id]

                        # save the old subjob result
                        expert_results[completed_job_id] = (
                            agent_result.get_workflow_result_message()
                        )

                        for new_subjob_id in new_job_graqph.vertices():
                            # add the new subjobs to the pending jobs
                            pending_job_ids.add(new_subjob_id)
                            # add the inputs for the new head subjobs
                            if not job_graph.predecessors(new_subjob_id):
                                pred_messages = [
                                    expert_results[pred_id]
                                    for pred_id in job_graph.predecessors(new_subjob_id)
                                ]
                                job_inputs[new_subjob_id] = AgentMessage(
                                    job_id=new_subjob_id,
                                    workflow_messages=pred_messages,
                                )

                    else:
                        expert_results[completed_job_id] = (
                            agent_result.get_workflow_result_message()
                        )

                    # remove from running jobs
                    del running_jobs[completed_job_id]

                # if no jobs are ready but some are pending, wait a bit
                if not completed_job_ids and running_jobs:
                    time.sleep(0.5)

    def stop_job_graph(self, job_id: str, stop_info: str) -> None:
        """Stop the job graph.

        When a specific job (original job / subjob) is stopped, this method is called to mark the
        entire current job as `STOPPED`, while other jobs without results (including subjobs and
        original jobs) are marked as `STOPPED`.

        Note that the running jobs are not stopped, since they are already set up in the
        ThreadPoolExecutor. The running jobs will be marked as `STOPPED` when they are finished.
        """
        # get the original job
        try:
            original_job: Job = self._job_service.get_original_job(original_job_id=job_id)
        except ValueError as e:
            job: SubJob = self._job_service.get_subjob(subjob_id=job_id)
            if not job.original_job_id:
                raise ValueError("The subjob is not assigned to an original job.") from e
            original_job = self._job_service.get_original_job(original_job_id=job.original_job_id)

        # save the final system message with the error information
        self._save_failed_or_stopped_message(original_job=original_job, message_payload=stop_info)

        # update all the subjobs which have not the final result
        self._stop_running_subjobs(original_job_id=original_job.id)

        # if the original job does not have a final result, mark it as stopped
        original_job_result = self._job_service.get_job_result(job_id=original_job.id)
        if not original_job_result.has_result():
            original_job_result.status = JobStatus.STOPPED
            self._job_service.save_job_result(job_result=original_job_result)

    def fail_job_graph(self, job_id: str, error_info: str) -> None:
        """Fail the job graph.

        When a specific job (original job / subjob) fails and it is necessary to stop the execution
        of the JobGraph, this method is called to mark the entire current job as `FAILED`, while
        other jobs without results (including subjobs and original jobs) are marked as `STOPPED`.
        """
        error_info += f"\n\nCheck the error details in path: '{SystemEnv.APP_ROOT}/logs/server.log'"
        job_result = self._job_service.get_job_result(job_id=job_id)

        if not job_result.has_result():
            # get the original job
            try:
                original_job: Job = self._job_service.get_original_job(original_job_id=job_id)
            except ValueError as e:
                job: SubJob = self._job_service.get_subjob(subjob_id=job_id)
                if not job.original_job_id:
                    raise ValueError("The subjob is not assigned to an original job.") from e
                original_job = self._job_service.get_original_job(
                    original_job_id=job.original_job_id
                )

            # save the final system message with the error information
            self._save_failed_or_stopped_message(
                original_job=original_job, message_payload=error_info
            )

            # mark the current job as failed
            job_result.status = JobStatus.FAILED
            self._job_service.save_job_result(job_result=job_result)

            # update all the subjobs which have not the final result
            self._stop_running_subjobs(original_job_id=original_job.id)

            # if the original job does not have a final result, mark it as stopped
            original_job_result = self._job_service.get_job_result(job_id=original_job.id)
            original_job_result.status = JobStatus.FAILED
            self._job_service.save_job_result(job_result=original_job_result)

    def recover_original_job(self, original_job_id: str) -> None:
        """Reconver the original job.

        When a specific original job is stopped and it is necessary to continue
        the execution of the JobGraph. If the leader has not decomposed the original job,
        this method is called to restart the job decomposition. If not, it will continue all the
        subjobs and mark them as `CREATED` to re-execute the job graph.
        """
        original_job = self._job_service.get_original_job(original_job_id=original_job_id)
        # mark the current job as finished
        original_job_result = self._job_service.get_job_result(job_id=original_job_id)
        if original_job_result.status == JobStatus.STOPPED:
            subjobs = self._job_service.get_subjobs(original_job_id=original_job_id)
            if len(subjobs) == 0:
                # if there are no subjobs, it means leader did not decompose the original job
                original_job_result.status = JobStatus.CREATED
                self._job_service.save_job_result(job_result=original_job_result)

                # start to execute the original job
                run_in_thread(self.execute_original_job, original_job=original_job)

            else:
                # if there are subjobs, it means leader decomposed the original job,
                # and waiting for the completion of the job graph
                original_job_result.status = JobStatus.RUNNING
                self._job_service.save_job_result(job_result=original_job_result)

                for sub_job in subjobs:
                    sub_job_result = self._job_service.get_job_result(job_id=sub_job.id)
                    if sub_job_result.status == JobStatus.STOPPED:
                        sub_job_result.status = JobStatus.CREATED
                        self._job_service.save_job_result(job_result=sub_job_result)

                # start to execute the job graph
                run_in_thread(self.execute_job_graph, original_job_id=original_job_id)

    def _stop_running_subjobs(self, original_job_id: str) -> None:
        """Stop all running jobs for the given original job."""
        # get all subjobs for the original job
        subjob_ids = self._job_service.get_subjob_ids(original_job_id=original_job_id)
        for subjob_id in subjob_ids:
            # get the subjob result
            subjob_result = self._job_service.get_job_result(job_id=subjob_id)
            if subjob_result.status == JobStatus.RUNNING:
                # mark the subjob as stopped
                subjob_result.status = JobStatus.STOPPED
                self._job_service.save_job_result(job_result=subjob_result)

    def _save_failed_or_stopped_message(self, original_job: Job, message_payload: str) -> None:
        """Save a message indicating the job has failed or stopped."""
        # save the final system message with the error information
        error_payload = (
            f"An error occurred during the execution of the job:\n\n{message_payload}\n\n"
            f'Please check the job `{original_job.id}` ("{original_job.goal[:10]}...") '
            "for more details. Or you can re-try to send your message."
        )
        original_job_id = original_job.id
        try:
            error_text_message: TextMessage = (
                self._message_service.get_text_message_by_job_id_and_role(
                    original_job_id, ChatMessageRole.SYSTEM
                )
            )
            error_text_message.set_payload(error_payload)
            self._message_service.save_message(message=error_text_message)
        except ValueError:
            error_text_message = TextMessage(
                payload=error_payload,
                job_id=original_job_id,
                session_id=original_job.session_id,
                assigned_expert_name=original_job.assigned_expert_name,
                role=ChatMessageRole.SYSTEM,
            )
            self._message_service.save_message(message=error_text_message)
            error_hybrid_message: HybridMessage = HybridMessage(
                instruction_message=error_text_message,
                job_id=original_job_id,
                role=ChatMessageRole.SYSTEM,
            )
            self._message_service.save_message(message=error_hybrid_message)

        # color: red
        print(f"\033[38;5;196m[ERROR]: {error_payload}\033[0m")

    def _execute_job(self, expert: Expert, agent_message: AgentMessage) -> AgentMessage:
        """Dispatch the job to the expert, and handle the result."""
        agent_result_message: AgentMessage = expert.execute(agent_message=agent_message)
        workflow_result: WorkflowMessage = agent_result_message.get_workflow_result_message()

        if workflow_result.status == WorkflowStatus.SUCCESS:
            return agent_result_message
        if workflow_result.status == WorkflowStatus.EXECUTION_ERROR:
            self.fail_job_graph(
                job_id=agent_message.get_job_id(),
                error_info=agent_result_message.get_lesson() or "Error info was missing.",
            )
            return agent_result_message
        if workflow_result.status == WorkflowStatus.INPUT_DATA_ERROR:
            # reexecute all the dependent jobs (predecessors)
            return agent_result_message
        if workflow_result.status == WorkflowStatus.JOB_TOO_COMPLICATED_ERROR:
            # reduce the life cycle of the subjob
            subjob: SubJob = self._job_service.get_subjob(subjob_id=agent_message.get_job_id())
            subjob.life_cycle -= 1
            subjob.is_legacy = True
            self._job_service.save_job(job=subjob)

            # the job is too complicated to be executed
            if subjob.life_cycle == 0:
                raise ValueError(
                    f"Job {subjob.id} runs out of life cycle. "
                    f"(initial life cycle: {SystemEnv.LIFE_CYCLE})"
                )

            # construct the job graph which will be replaced by the new sub job graph
            replaced_job_graph: JobGraph = JobGraph()
            replaced_job_graph.add_vertex(subjob.id)

            # reexecute the subjob with a new sub-subjob
            new_job_graqph: JobGraph = self.execute(agent_message=agent_result_message)
            self._job_service.replace_subgraph(
                original_job_id=subjob.id,
                new_subgraph=new_job_graqph,
                old_subgraph=replaced_job_graph,
            )

        raise ValueError(
            f"Job {agent_message.get_job_id()} failed with an unexpected status: "
            f"{workflow_result.status.value}. Please check the job graph status."
        )

    def _validate_job_dict(
        self, job_dict: Dict[str, Dict[str, str]], expert_names: List[str]
    ) -> None:
        """Validate the structure and content of the job_dict."""
        if not isinstance(job_dict, dict):
            raise ValueError("Decomposition result must be a dictionary.")

        if not job_dict:
            raise ValueError("Decomposition result dictionary cannot be empty.")

        all_task_ids = set(job_dict.keys())

        for task_id, task_data in job_dict.items():
            if not isinstance(task_data, dict):
                raise ValueError(f"Task '{task_id}' data must be a dictionary.")

            missing_keys = subjob_required_keys - set(task_data.keys())
            if missing_keys:
                raise ValueError(f"Task '{task_id}' is missing required keys: {missing_keys}")

            # convert list/dict to string for specific fields before type validation
            for key_to_convert in ["goal", "context", "completion_criteria", "thinking"]:
                if key_to_convert in task_data:
                    if isinstance(task_data[key_to_convert], list):
                        task_data[key_to_convert] = "\n".join(map(str, task_data[key_to_convert]))
                    elif isinstance(task_data[key_to_convert], dict):
                        task_data[key_to_convert] = json.dumps(task_data[key_to_convert])

            # validate types
            for key in ["goal", "context", "completion_criteria", "assigned_expert", "thinking"]:
                if not isinstance(task_data[key], str):
                    raise ValueError(f"Task '{task_id}' key '{key}' must be a string.")

            if not isinstance(task_data["dependencies"], list):
                raise ValueError(f"Task '{task_id}' key 'dependencies' must be a list.")

            # validate dependencies exist
            for dep_id in task_data["dependencies"]:
                if dep_id not in all_task_ids:
                    raise ValueError(
                        f"Task '{task_id}' has an invalid dependency: '{dep_id}' does not exist."
                    )

            # validate assigned expert
            expert_name = task_data["assigned_expert"]
            if expert_name not in expert_names:
                raise ValueError(
                    f"Task '{task_id}' assigned expert '{expert_name}' not found "
                    f"in available experts: {expert_names}"
                )

            # optional: validate thinking is not empty or add more specific checks
            if not task_data["thinking"].strip():
                print(
                    f"\033[38;5;208m[WARNING]: Task '{task_id}' has empty 'thinking' field.\033[0m"
                )

    @property
    def state(self) -> LeaderState:
        """Get the leader state."""
        return self._leader_state
