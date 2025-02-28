import asyncio

from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


async def main():
    """Main function."""
    mas = AgenticService("Chat2Graph")
    mas.load("app/core/sdk/chat2graph.yml")

    # set the user message
    user_message = TextMessage(
        # payload="通过工具来阅读原文，我需要对《三国演义》中的关系进行*复杂*的图建模（为知识图谱做准备），这个建模能够覆盖掉文本以及一些文本细节（5 个以上 vertices labels，和同等量级的 edge labels。"
        payload="将给定的文本的所有的数据导入到图数据库中（总共至少导入 100 个三元组关系来满足知识图谱的数据丰富性）。拆分成一个 subtask"
    )

    # submit the job
    session = mas.session()
    job_wrapper = await session.submit(user_message)
    service_message = await session.wait(job_wrapper)

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
