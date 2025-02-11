import asyncio

from app.core.sdk.legacy.graph_query import get_graph_query_workflow
from app.core.model.job import SubJob
from app.core.reasoner.dual_model_reasoner import DualModelReasoner


async def main():
    """Main function"""
    workflow = get_graph_query_workflow()

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="查询节点，vertex_type为entity，查询条件为节点的属性description包含'github用户'"
        "图数据库的主题是TuGraph。可能需要调用相关的工具（通过函数调用）来操作图数据库。",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
