import networkx as nx  # type: ignore

from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.model.job import SubJob
from app.core.model.job_graph import JobGraph
from app.core.model.message import AgentMessage
from app.core.prompt.job import JOB_DECOMPOSITION_OUTPUT_SCHEMA, JOB_DECOMPOSITION_PROMPT
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.service.job_service import JobService
from app.core.service.service_factory import ServiceFactory
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow

ServiceFactory.initialize()


def main():
    """Main function."""
    # initialize
    reasoner = MonoModelReasoner()
    decomp_operator_config = OperatorConfig(
        id="job_decomp_operator_id",
        instruction=JOB_DECOMPOSITION_PROMPT,
        actions=[],
        output_schema=JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    )
    decomposition_operator = Operator(config=decomp_operator_config)

    leader_workflow = DbgptWorkflow()
    leader_workflow.add_operator(decomposition_operator)
    config = AgentConfig(profile="test", reasoner=reasoner, workflow=leader_workflow)
    leader = Leader(agent_config=config)

    goal = """从文本中提取出关键实体类型，为后续的图数据库模型构建奠定基础。"""
    job = SubJob(session_id="test_session_id", id="test_task_id", goal=goal, context="")

    expert_profile_1 = AgentConfig(
        profile=Profile(
            name="Data Collector",
            description="He can collect data",
        ),
        reasoner=reasoner,
        workflow=DbgptWorkflow(),
    )
    expert_profile_2 = AgentConfig(
        profile=Profile(
            name="Entity Classifier",
            description="He can classify entities",
        ),
        reasoner=reasoner,
        workflow=DbgptWorkflow(),
    )
    expert_profile_3 = AgentConfig(
        profile=Profile(
            name="Result Analyst",
            description="He can analyze results",
        ),
        reasoner=reasoner,
        workflow=DbgptWorkflow(),
    )
    leader.state.create_expert(expert_profile_1)
    leader.state.create_expert(expert_profile_2)
    leader.state.create_expert(expert_profile_3)

    # configure the initial job graph
    initial_job_graph: JobGraph = JobGraph()
    initial_job_graph.add_vertex(id=job.id, job=job)
    job_service: JobService = JobService()
    job_service.set_job_graph(original_job_id=job.id, job_graph=initial_job_graph)

    # decompose the job
    job_graph = leader.execute(AgentMessage(job_id=job.id))

    print("=== Decomposed Subtasks ===")
    for subjob_id in nx.topological_sort(job_graph.get_graph()):
        subjob: SubJob = job_service.get_subjob(subjob_id)
        expert_id: str = subjob.expert_id
        expert: Expert = leader.state.get_expert_by_id(expert_id)
        expert_name: str = expert._profile.name

        print(f"\nAssigned Expert: {expert_name}")
        print("Goal:", subjob.goal)
        print("Context:", subjob.context)


if __name__ == "__main__":
    main()
