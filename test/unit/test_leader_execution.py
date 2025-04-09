from typing import List, Optional, cast
from uuid import uuid4

from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.leader import Leader
from app.core.common.type import JobStatus
from app.core.dal.init_db import init_db
from app.core.model.job import Job, SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.job_result import JobResult
from app.core.model.message import AgentMessage, MessageType, WorkflowMessage
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.sdk.agentic_service import AgenticService
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.service.reasoner_service import ReasonerService
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow

AgenticService()
job_service: JobService = JobService.instance
init_db()


class TestAgentOperator(Operator):
    """base test operator for agent integration test"""

    def __init__(self, id: str):
        self._config = OperatorConfig(id=id, instruction="", actions=[])

    def execute(
        self,
        reasoner: DualModelReasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        # job1: generate numbers
        if self._config.id == "gen":
            result = "\n" + job.context.strip()
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

        # job2: multiply by 2
        elif self._config.id == "mult":
            numbers = [int(x) for x in previous_expert_outputs[-1].scratchpad.strip().split()]
            result = " ".join(str(x * 2) for x in numbers)
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

        # job3: add 10
        elif self._config.id == "add":
            numbers = [int(x) for x in previous_expert_outputs[-1].scratchpad.strip().split()]
            result = " ".join(str(x + 10) for x in numbers)
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

        # job4: sum
        elif self._config.id == "sum":
            numbers = [int(x) for x in previous_expert_outputs[-1].scratchpad.strip().split()]
            result = str(sum(numbers))
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

        # job5: format result
        elif self._config.id == "format":
            result = f"Final Result\n:{'{}'.join([msg.scratchpad for msg in previous_expert_outputs])}".format(
                "\n"
            )
            return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

        raise ValueError(f"Unknown operator id: {self._config.id}")


def test_agent_job_graph():
    """test job graph message flow.

    graph structure:
              Task2 (x2)
            ↗           ↘
    Task1 (Gen)           Task5 (Format) [Terminal]
            ↘           ↗
              Task3 (+10) → Task4 (Sum) [Terminal]
    """
    # init components
    reasoner_service: ReasonerService = ReasonerService.instance
    reasoner = reasoner_service.get_reasoner()

    agent_config = AgentConfig(
        profile=Profile(name="Leader"), reasoner=reasoner, workflow=DbgptWorkflow()
    )
    leader = Leader(agent_config=agent_config)

    # create jobs
    jobs: List[SubJob] = []
    initial_numbers = "1 2 3 4 5"
    for i, (id, goal) in enumerate(
        [
            ("job_1" + str(uuid4()), "Generate numbers"),
            ("job_2" + str(uuid4()), "Multiply by 2"),
            ("job_3" + str(uuid4()), "Add 10"),
            ("job_4" + str(uuid4()), "Sum the numbers"),
            ("job_5" + str(uuid4()), "Format final result"),
        ]
    ):
        jobs.append(
            SubJob(
                id=id,
                session_id="test_session_id",
                goal=goal,
                context=initial_numbers if i == 0 else "",
                output_schema="string",
            )
        )

    # create operators and workflows
    operators = [
        ("gen", "Expert 1"),
        ("mult", "Expert 2"),
        ("add", "Expert 3"),
        ("sum", "Expert 4"),
        ("format", "Expert 5"),
    ]

    for op_id, expert_name in operators:
        workflow = DbgptWorkflow()
        workflow.add_operator(TestAgentOperator(op_id))

        leader.state.create_expert(
            agent_config=AgentConfig(
                profile=Profile(name=expert_name, description=f"Expert for {op_id}"),
                reasoner=reasoner,
                workflow=workflow,
            ),
        )

    # build job graph
    original_job: Job = Job(id="test_original_job_id" + str(uuid4()), goal="Test Job Graph")
    job_service.save_job(job=original_job)
    job_service.add_subjob(
        original_job_id=original_job.id,
        job=jobs[0],
        expert_id=leader.state.get_expert_by_name("Expert 1").get_id(),
        predecessors=[],
        successors=[jobs[1], jobs[2]],
    )

    job_service.add_subjob(
        original_job_id=original_job.id,
        job=jobs[1],
        expert_id=leader.state.get_expert_by_name("Expert 2").get_id(),
        predecessors=[jobs[0]],
        successors=[jobs[4]],
    )

    job_service.add_subjob(
        original_job_id=original_job.id,
        job=jobs[2],
        expert_id=leader.state.get_expert_by_name("Expert 3").get_id(),
        predecessors=[jobs[0]],
        successors=[jobs[3]],
    )

    job_service.add_subjob(
        original_job_id=original_job.id,
        job=jobs[3],
        expert_id=leader.state.get_expert_by_name("Expert 4").get_id(),
        predecessors=[jobs[2]],
        successors=[],
    )

    job_service.add_subjob(
        original_job_id=original_job.id,
        job=jobs[4],
        expert_id=leader.state.get_expert_by_name("Expert 5").get_id(),
        predecessors=[jobs[1], jobs[2]],
        successors=[],
    )

    # execute job graph
    leader.execute_job_graph(original_job_id=original_job.id)
    job_graph: JobGraph = job_service.get_job_graph(original_job_id=original_job.id)
    tail_vertices = [vertex for vertex in job_graph.vertices() if job_graph.out_degree(vertex) == 0]
    terminal_job_results: List[JobResult] = [
        job_service.query_original_job_result(vertex) for vertex in tail_vertices
    ]

    # verify we only get messages from terminal vertices (job4 and job5)
    assert len(tail_vertices) == 2, "Should receive 2 messages from terminal vertices"

    # extract job4 (sum) and job5 (format) results
    job4_result = next(result for result in terminal_job_results if "job_4" in result.job_id)
    job5_result = next(result for result in terminal_job_results if "job_5" in result.job_id)

    # verify job statuses
    assert job4_result.status == JobStatus.FINISHED
    assert job5_result.status == JobStatus.FINISHED

    # verify job4 result (sum of numbers after adding 10)
    # original: 1 2 3 4 5 -> after +10: 11 12 13 14 15 -> sum: 65
    message_service: MessageService = MessageService.instance
    job4_result_message: AgentMessage = cast(
        AgentMessage,
        message_service.get_message_by_job_id(
            job_id=job_service.get_subjob(subjob_id=job4_result.job_id).id,
            message_type=MessageType.AGENT_MESSAGE,
        )[0],
    )

    assert job4_result_message.get_payload() == "65"

    # verify job5 result (format of multiply by 2 and add 10 results)
    # job5_output = job5_result.message.get_payload()
    job5_result_message: AgentMessage = cast(
        AgentMessage,
        message_service.get_message_by_job_id(
            job_id=job5_result.job_id, message_type=MessageType.AGENT_MESSAGE
        )[0],
    )
    assert "2 4 6 8 10" in job5_result_message.get_payload()
    assert "11 12 13 14 15" in job5_result_message.get_payload()
    assert job5_result_message.get_payload().startswith("Final Result")
