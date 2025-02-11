import asyncio

from app.agent.graph_agent.data_importation import get_data_importation_workflow
from app.agent.job import SubJob
from app.agent.reasoner.dual_model_reasoner import DualModelReasoner


async def main():
    """Main function to run the data import."""
    workflow = get_data_importation_workflow()

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="目前我们的问题的背景是，通过函数读取文档的内容，结合当前图数据库中的图模型完成实体和关系的数据抽取和数据的导入，并输出导入结果。"
        "你至少需要导入 100 个数据点。",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
