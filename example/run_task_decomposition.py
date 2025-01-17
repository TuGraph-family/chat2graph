import asyncio

import networkx as nx

from app.agent.agent import AgentConfig, Profile
from app.agent.expert import Expert
from app.agent.job import Job
from app.agent.leader import Leader
from app.agent.reasoner.mono_model_reasoner import MonoModelReasoner
from app.agent.workflow.operator.operator import Operator
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.prompt.agent import JOB_DECOMPOSITION_OUTPUT_SCHEMA
from app.plugin.dbgpt.dbgpt_workflow import DbgptWorkflow


async def main():
    """Main function."""
    # initialize
    reasoner = MonoModelReasoner()
    decomp_operator_config = OperatorConfig(
        id="job_decomp_operator_id",
        instruction="",
        actions=[],
        output_schema=JOB_DECOMPOSITION_OUTPUT_SCHEMA,
    )
    decomposition_operator = Operator(config=decomp_operator_config)

    leader_workflow = DbgptWorkflow()
    leader_workflow.add_operator(decomposition_operator)
    config = AgentConfig(profile="test", reasoner=reasoner, workflow=leader_workflow)
    leader = Leader(agent_config=config)
    goal = """从文本中提取出关键实体类型，为后续的图数据库模型构建奠定基础。"""
    job = Job(session_id="test_session_id", id="test_task_id", goal=goal, context="")

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
    leader._leader_state.add_expert_config("Data Collector", expert_profile_1)
    leader._leader_state.add_expert_config("Entity Classifier", expert_profile_2)
    leader._leader_state.add_expert_config("Result Analyst", expert_profile_3)

    # decompose the job
    jobs_graph = await leader._execute_decomp_workflow(job=job, num_subjobs=3)

    print("=== Decomposed Subtasks ===")
    for subjob_id in nx.topological_sort(jobs_graph):
        subjob: Job = jobs_graph.nodes[subjob_id]["job"]
        expert_id: str = jobs_graph.nodes[subjob_id]["expert_id"]
        expert: Expert = leader._leader_state.get_or_create_expert_by_id(expert_id)
        expert_name: str = expert._profile.name

        print(f"\nAssigned Expert: {expert_name}")
        print("Goal:", subjob.goal)
        print("Context:", subjob.context)

    # assert len(leader._leader_state.list_expert_assignments().keys()) == 3

    # execute the leader's main workflow
    # await leader.execute()


if __name__ == "__main__":
    asyncio.run(main())
