import asyncio
from typing import List, Optional

from app.agent.agent import AgentConfig, Profile
from app.agent.graph import JobGraph
from app.agent.job import Job, SubJob
from app.agent.leader import Leader
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.reasoner import Reasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.memory.message import WorkflowMessage
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from app.service.job_service import JobService


class BaseTestOperator(Operator):
    """Base test operator"""

    def __init__(self, id: str):
        # Did not Call super().__init__(), because it is a test class
        self._config = OperatorConfig(id=id, instruction="", actions=[])

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        raise NotImplementedError


class NumberGeneratorOperator(BaseTestOperator):
    """Generate a sequence of numbers"""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        last_line = job.context.strip().split("\n")[-1]
        numbers = [int(x) for x in last_line.split()]
        result = "\n" + " ".join(str(x) for x in numbers)
        print(f"NumberGenerator output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result})


class MultiplyByTwoOperator(BaseTestOperator):
    """Multiply each number by 2"""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        last_line = workflow_messages[-1].scratchpad.strip()
        numbers = [int(x) for x in last_line.split()]
        result = " ".join(str(x * 2) for x in numbers)
        print(f"MultiplyByTwo output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result})


class AddTenOperator(BaseTestOperator):
    """Add 10 to each number"""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        last_line = workflow_messages[-1].scratchpad.strip()
        numbers = [int(x) for x in last_line.split()]
        result = " ".join(str(x + 10) for x in numbers)
        print(f"AddTen output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result})


class SumOperator(BaseTestOperator):
    """Sum all numbers"""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        last_line = workflow_messages[-1].scratchpad.strip()
        numbers = [int(x) for x in last_line.split()]
        result = str(sum(numbers))
        print(f"Sum output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result})


class FormatResultOperator(BaseTestOperator):
    """Format the final result"""

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        result = (
            f"Final Result\n:{'{}'.join([msg.scratchpad for msg in workflow_messages])}".format(
                "\n"
            )
        )
        print(f"Format output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result})


async def main():
    """Main function for testing leader execute functionality."""
    # initialize components
    reasoner = DualModelReasoner()
    agent_config = AgentConfig(profile="test", reasoner=reasoner, workflow=DbgptWorkflow())
    leader = Leader(agent_config=agent_config)

    # create jobs with more complex descriptions
    # Task Graph Structure:
    #
    #              Task2 (×2)
    #            ↗           ↘
    # Task1 (Gen)             Task5 (Format)
    #            ↘           ↗
    #              Task3 (+10)
    #                 ↓
    #              Task4 (Sum)

    job_1 = SubJob(
        id="job_1",
        session_id="test_session_id",
        goal="Generate numbers",
        context="1 2 3 4 5",
        output_schema="string",
    )

    job_2 = SubJob(
        id="job_2",
        session_id="test_session_id",
        goal="Multiply numbers by 2",
        context="",
        output_schema="string",
    )

    job_3 = SubJob(
        id="job_3",
        session_id="test_session_id",
        goal="Add 10 to numbers",
        context="",
        output_schema="string",
    )

    job_4 = SubJob(
        id="job_4",
        session_id="test_session_id",
        goal="Sum the numbers",
        context="",
        output_schema="string",
    )

    job_5 = SubJob(
        id="job_5",
        session_id="test_session_id",
        goal="Format final result",
        context="",
        output_schema="string",
    )

    # create workflows for each job
    workflow1 = DbgptWorkflow()
    workflow1.add_operator(NumberGeneratorOperator("gen"))

    workflow2 = DbgptWorkflow()
    workflow2.add_operator(MultiplyByTwoOperator("mult"))

    workflow3 = DbgptWorkflow()
    workflow3.add_operator(AddTenOperator("add"))

    workflow4 = DbgptWorkflow()
    workflow4.add_operator(SumOperator("sum"))

    workflow5 = DbgptWorkflow()
    workflow5.add_operator(FormatResultOperator("format"))

    workflows = [workflow1, workflow2, workflow3, workflow4, workflow5]

    # create expert profiles
    for i, workflow in enumerate(workflows):
        leader.state.create_expert(
            agent_config=AgentConfig(
                profile=Profile(name=f"Expert {i + 1}", description=f"Expert {i + 1}"),
                reasoner=reasoner,
                workflow=workflow,
            ),
        )

    job_service: JobService = JobService()
    # Create job graph structure
    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_1,
        expert=leader.state.get_expert_by_name("Expert 1"),
        predecessors=[],
        successors=[job_2, job_3],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_2,
        expert=leader.state.get_expert_by_name("Expert 2"),
        predecessors=[job_1],
        successors=[job_5],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_3,
        expert=leader.state.get_expert_by_name("Expert 3"),
        predecessors=[job_1],
        successors=[job_4],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_4,
        expert=leader.state.get_expert_by_name("Expert 4"),
        predecessors=[job_3],
        successors=[],
    )

    job_service.add_job(
        original_job_id="test_original_job_id",
        job=job_5,
        expert=leader.state.get_expert_by_name("Expert 5"),
        predecessors=[job_2, job_3],
        successors=[],
    )
    # execute the job graph
    print("\n=== Starting Leader Execute TestTest ===")

    # get the job graph and expert assignments
    job_graph: JobGraph = await leader.execute_job_graph(
        job_graph=job_service.get_job_graph("test_original_job_id")
    )
    tail_nodes = [node for node in job_graph.nodes() if job_graph.out_degree(node) == 0]

    print("\n=== Execution Results ===")
    for tail_node in tail_nodes:
        job = job_graph.get_job(tail_node)
        job_result = job_graph.get_job_result(tail_node)
        if not job_result:
            print(f"Job {tail_node} is not completed yet.")
            continue
        print(f"\nTask {job.id}:")
        print(f"Status: {job_result.status}")
        print(f"Output: {job_result.result.get_payload()}")
        print("-" * 50)


if __name__ == "__main__":
    asyncio.run(main())

# === Starting Leader Execute TestTest ===
# NumberGenerator output: 1 2 3 4 5
# --------------------------------------------------
# MultiplyByTwo output: 2 4 6 8 10
# --------------------------------------------------
# AddTen output: 11 12 13 14 15
# --------------------------------------------------
# Sum output: 65
# --------------------------------------------------
# Format output: Final Result:
# 2 4 6 8 10
# 11 12 13 14 15
# --------------------------------------------------
