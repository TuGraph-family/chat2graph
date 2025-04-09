from typing import List, Optional, cast

from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.leader import Leader
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.job import Job, SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.message import AgentMessage, MessageType, WorkflowMessage
from app.core.reasoner.reasoner import Reasoner
from app.core.service.job_service import JobService
from app.core.service.message_service import MessageService
from app.core.service.reasoner_service import ReasonerService
from app.core.service.service_factory import ServiceFactory
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow

DaoFactory().initialize(DbSession())
ServiceFactory().initialize()


class BaseTestOperator(Operator):
    """Base test operator"""

    def __init__(self, id: str):
        # Did not Call super().__init__(), because it is a test class
        self._config = OperatorConfig(id=id, instruction="", actions=[])

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        raise NotImplementedError


class NumberGeneratorOperator(BaseTestOperator):
    """Generate a sequence of numbers"""

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        last_line = job.context.strip().split("\n")[-1]
        numbers = [int(x) for x in last_line.split()]
        result = "\n" + " ".join(str(x) for x in numbers)
        print(f"NumberGenerator output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)


class MultiplyByTwoOperator(BaseTestOperator):
    """Multiply each number by 2"""

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        last_line = workflow_messages[-1].scratchpad.strip()
        numbers = [int(x) for x in last_line.split()]
        result = " ".join(str(x * 2) for x in numbers)
        print(f"MultiplyByTwo output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)


class AddTenOperator(BaseTestOperator):
    """Add 10 to each number"""

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        last_line = workflow_messages[-1].scratchpad.strip()
        numbers = [int(x) for x in last_line.split()]
        result = " ".join(str(x + 10) for x in numbers)
        print(f"AddTen output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)


class SumOperator(BaseTestOperator):
    """Sum all numbers"""

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        assert workflow_messages is not None, "Workflow messages should not be None"
        last_line = workflow_messages[-1].scratchpad.strip()
        numbers = [int(x) for x in last_line.split()]
        result = str(sum(numbers))
        print(f"Sum output: {result}")
        print("-" * 50)
        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)


class FormatResultOperator(BaseTestOperator):
    """Format the final result"""

    def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
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
        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)


def main():
    """Main function for testing leader execute functionality."""
    # initialize components
    reasoner_service: ReasonerService = ReasonerService.instance
    reasoner = reasoner_service.get_reasoner()
    agent_config = AgentConfig(
        profile=Profile(name="Academic_reviewer"), reasoner=reasoner, workflow=DbgptWorkflow()
    )
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

    job = Job(id="test_original_job_id", session_id="test_session_id", goal="Test Job")
    job_1 = SubJob(
        id="job_1",
        original_job_id=job.id,
        session_id="test_session_id",
        goal="Generate numbers",
        context="1 2 3 4 5",
        output_schema="string",
    )

    job_2 = SubJob(
        id="job_2",
        original_job_id=job.id,
        session_id="test_session_id",
        goal="Multiply numbers by 2",
        context="",
        output_schema="string",
    )

    job_3 = SubJob(
        id="job_3",
        original_job_id=job.id,
        session_id="test_session_id",
        goal="Add 10 to numbers",
        context="",
        output_schema="string",
    )

    job_4 = SubJob(
        id="job_4",
        original_job_id=job.id,
        session_id="test_session_id",
        goal="Sum the numbers",
        context="",
        output_schema="string",
    )

    job_5 = SubJob(
        id="job_5",
        original_job_id=job.id,
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

    job_service: JobService = JobService.instance
    job_service.save_job(job=job)
    # Create job graph structure
    job_service.add_subjob(
        original_job_id="test_original_job_id",
        job=job_1,
        expert_id=leader.state.get_expert_by_name("Expert 1").get_id(),
        predecessors=[],
        successors=[job_2, job_3],
    )

    job_service.add_subjob(
        original_job_id="test_original_job_id",
        job=job_2,
        expert_id=leader.state.get_expert_by_name("Expert 2").get_id(),
        predecessors=[job_1],
        successors=[job_5],
    )

    job_service.add_subjob(
        original_job_id="test_original_job_id",
        job=job_3,
        expert_id=leader.state.get_expert_by_name("Expert 3").get_id(),
        predecessors=[job_1],
        successors=[job_4],
    )

    job_service.add_subjob(
        original_job_id="test_original_job_id",
        job=job_4,
        expert_id=leader.state.get_expert_by_name("Expert 4").get_id(),
        predecessors=[job_3],
        successors=[],
    )

    job_service.add_subjob(
        original_job_id="test_original_job_id",
        job=job_5,
        expert_id=leader.state.get_expert_by_name("Expert 5").get_id(),
        predecessors=[job_2, job_3],
        successors=[],
    )
    # execute the job graph
    print("\n=== Starting Leader Execute TestTest ===")

    # get the job graph and expert assignments
    leader.execute_job_graph(original_job_id="test_original_job_id")
    job_graph: JobGraph = job_service.get_job_graph("test_original_job_id")
    tail_vertices = [vertex for vertex in job_graph.vertices() if job_graph.out_degree(vertex) == 0]

    message_service: MessageService = MessageService.instance
    print("\n=== Execution Results ===")
    for tail_vertex in tail_vertices:
        job = job_service.get_subjob(tail_vertex)
        job_result = job_service.query_original_job_result(tail_vertex)
        if not job_result:
            print(f"Job {tail_vertex} is not completed yet.")
            continue
        print(f"\nTask {job.id}:")
        print(f"Status: {job_result.status}")
        print(
            "Output: "
            + {
                cast(
                    AgentMessage,
                    message_service.get_message_by_job_id(
                        job_id=job.id, message_type=MessageType.AGENT_MESSAGE
                    )[0],
                ).get_payload()
            }
        )
        print("-" * 50)


if __name__ == "__main__":
    main()

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
