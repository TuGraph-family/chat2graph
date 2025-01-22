import asyncio

from app.agentic_service import AgenticService
from app.memory.message import TextMessage


async def main():
    """Main function."""
    agentic_service = AgenticService()

    # set the session ID
    session_id = "test_session_id"

    # set the user message
    user_message = TextMessage(
        payload=(
            "首先我需要对《三国演义》中的关系进行建模，然后我会给你《三国演义》的部分文档，你需要把数据导入到图数据库中（建立一个全面的知识图谱）。最后基于构建好的图数据库，我希望了解曹操的故事以及影响力。"
            "《三国演义》中的曹操是一个充满争议的历史人物。他既是一个雄才大略的枭雄，也是一个爱才惜才的领袖；既是一个残暴的统治者，也是一个浪漫的诗人。通过图谱分析，我们将从数据的角度来解读这位复杂的历史人物。"
        ),
    )

    # submit the job
    session = agentic_service.session(session_id=session_id)
    job = await session.submit(message=user_message)
    service_message = await session.wait(job.id)

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
