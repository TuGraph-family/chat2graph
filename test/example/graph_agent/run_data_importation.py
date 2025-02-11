import asyncio

from app.core.sdk.legacy.data_importation import get_data_importation_workflow
from app.core.model.job import SubJob
from app.core.reasoner.dual_model_reasoner import DualModelReasoner


async def main():
    """Main function to run the data import."""
    workflow = get_data_importation_workflow()

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="目前我们的问题的背景是：阅读《三国演义》的第50回，结合当前图数据库中的图模型完成实体和关系的数据抽取和数据的导入，并输出导入结果。",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
