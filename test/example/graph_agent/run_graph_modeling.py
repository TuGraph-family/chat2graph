import asyncio

from app.core.model.job import SubJob
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.sdk.legacy.graph_modeling import get_graph_modeling_workflow


async def main():
    """Main function"""
    workflow = get_graph_modeling_workflow()

    job = SubJob(
        id="test_job_id",
        session_id="test_session_id",
        goal="「任务」",
        context="目前的问题的背景是，通过函数读取文档第50章节的内容，生成知识图谱图数据库的模式"
        "（Graph schema/label），最后调用相关函数来帮助在图数据库中创建 labels。"
        "文档的主题是三国演义。可能需要调用相关的工具（通过函数调用）来操作图数据库。",
    )
    reasoner = DualModelReasoner()

    result = await workflow.execute(job=job, reasoner=reasoner)

    print(f"Final result:\n{result.scratchpad}")


if __name__ == "__main__":
    asyncio.run(main())
