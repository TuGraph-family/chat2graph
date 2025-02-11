from typing import List, Optional

import pytest

from app.agent.agent import AgentConfig, Profile
from app.agent.graph import JobGraph
from app.agent.job import Job, SubJob
from app.agent.job_result import JobResult
from app.agent.leader import Leader
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.type import JobStatus
from app.memory.message import WorkflowMessage
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.service.job_service import JobService


class TestAgentOperator(Operator):
    """base test operator for agent integration test"""

    def __init__(self, id: str):
        self._config = OperatorConfig(id=id, instruction="", actions=[])

    async def execute(
        self,
        reasoner: DualModelReasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        # job1: generate numbers
        if self._config.id == "gen":
            result = "\n" + job.context.strip()
            return WorkflowMessage(payload={"scratchpad": result})

        # job2: multiply by 2
        elif self._config.id == "mult":
            numbers = [int(x) for x in workflow_messages[-1].scratchpad.strip().split()]
            result = " ".join(str(x * 2) for x in numbers)
            return WorkflowMessage(payload={"scratchpad": result})

        # job3: add 10
        elif self._config.id == "add":
            numbers = [int(x) for x in workflow_messages[-1].scratchpad.strip().split()]
            result = " ".join(str(x + 10) for x in numbers)
            return WorkflowMessage(payload={"scratchpad": result})

        # job4: sum
        elif self._config.id == "sum":
            numbers = [int(x) for x in workflow_messages[-1].scratchpad.strip().split()]
            result = str(sum(numbers))
            return WorkflowMessage(payload={"scratchpad": result})

        # job5: format result
        elif self._config.id == "format":
            result = (
                f"Final Result\n:{'{}'.join([msg.scratchpad for msg in workflow_messages])}".format(
                    "\n"
                )
            )
            return WorkflowMessage(payload={"scratchpad": result})

        raise ValueError(f"Unknown operator id: {self._config.id}")


@pytest.mark.asyncio
async def test_agent_job_graph():
    """test job graph message flow.

    graph structure:
              Task2 (x2)
            ↗           ↘
    Task1 (Gen)           Task5 (Format) [Terminal]
            ↘           ↗
              Task3 (+10) → Task4 (Sum) [Terminal]
    """
    # init components
    reasoner = DualModelReasoner()
    agent_config = AgentConfig(profile="test", reasoner=reasoner, workflow=DbgptWorkflow())
    leader = Leader(agent_config=agent_config)

    # create jobs
    jobs = []
    initial_numbers = "1 2 3 4 5"
    for i, (id, goal) in enumerate(
        [
            ("job_1", "Generate numbers"),
            ("job_2", "Multiply by 2"),
            ("job_3", "Add 10"),
            ("job_4", "Sum the numbers"),
            ("job_5", "Format final result"),
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
    job_service: JobService = JobService()
    job_service.add_job(
        original_job_id="test_original_job_id",
        job=jobs[0],
        expert=leader.state.get_expert_by_name("Expert 1"),
        predecessors=[],
        successors=[jobs[1], jobs[2]],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=jobs[1],
        expert=leader.state.get_expert_by_name("Expert 2"),
        predecessors=[jobs[0]],
        successors=[jobs[4]],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=jobs[2],
        expert=leader.state.get_expert_by_name("Expert 3"),
        predecessors=[jobs[0]],
        successors=[jobs[3]],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=jobs[3],
        expert=leader.state.get_expert_by_name("Expert 4"),
        predecessors=[jobs[2]],
        successors=[],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=jobs[4],
        expert=leader.state.get_expert_by_name("Expert 5"),
        predecessors=[jobs[1], jobs[2]],
        successors=[],
    )

    # execute job graph
    job_graph: JobGraph = await leader.execute_job_graph(
        job_graph=job_service.get_job_graph(job_id="test_original_job_id")
    )
    tail_nodes = [node for node in job_graph.nodes() if job_graph.out_degree(node) == 0]
    terminal_job_results: List[JobResult] = [job_graph.get_job_result(node) for node in tail_nodes]

    # verify we only get messages from terminal nodes (job4 and job5)
    assert len(tail_nodes) == 2, "Should receive 2 messages from terminal nodes"

    # extract job4 (sum) and job5 (format) results
    job4_result = next(result for result in terminal_job_results if result.job_id == "job_4")
    job5_result = next(result for result in terminal_job_results if result.job_id == "job_5")

    # verify job statuses
    assert job4_result.status == JobStatus.FINISHED
    assert job5_result.status == JobStatus.FINISHED

    # verify job4 result (sum of numbers after adding 10)
    # original: 1 2 3 4 5 -> after +10: 11 12 13 14 15 -> sum: 65
    assert job4_result.result.get_payload() == "65"

    # verify job5 result (format of multiply by 2 and add 10 results)
    job5_output = job5_result.result.get_payload()
    assert "2 4 6 8 10" in job5_output
    assert "11 12 13 14 15" in job5_output
    assert job5_output.startswith("Final Result")
