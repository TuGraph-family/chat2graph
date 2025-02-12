import asyncio

from app.core.model.job import SubJob
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.sdk.legacy.graph_analysis import get_graph_analysis_workflow


async def main():
    """Main function"""
    workflow = get_graph_analysis_workflow()

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="用户目前的需求是想知道在当前图数据库中，影响力最大的节点是哪个？我需要通过执行算法来找到这个节点。",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
