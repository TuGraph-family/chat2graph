import networkx as nx  # type: ignore

from app.core.agent.agent import AgentConfig, Profile
from app.core.agent.expert import Expert
from app.core.agent.leader import Leader
from app.core.model.job import Job, SubJob
from app.core.model.message import AgentMessage
from app.core.prompt.job_decomposition import (
    JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    JOB_DECOMPOSITION_PROMPT,
)
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.service.job_service import JobService
from app.core.workflow.operator import Operator
from app.core.workflow.operator_config import OperatorConfig
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow
from test.resource.init_server import init_server

init_server()


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
    config = AgentConfig(
        profile=Profile(name="Leader"), reasoner=reasoner, workflow=leader_workflow
    )
    leader = Leader(agent_config=config)

    job_service: JobService = JobService.instance
    goal = """从文本中提取出关键实体类型，为后续的图数据库模型构建奠定基础。"""
    job = Job(session_id="test_session_id", id="test_task_id", goal=goal, context="")
    job_service.save_job(job)

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

    # decompose the job
    job_graph = leader.execute(AgentMessage(job_id=job.id))

    print("=== Decomposed Subtasks ===")
    job_service: JobService = JobService.instance
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
