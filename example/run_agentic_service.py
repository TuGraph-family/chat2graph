import asyncio

from app.agentic_service import AgenticService
from app.memory.message import UserMessage


async def main():
    """Main function."""
    agentic_service = AgenticService()

    user_message = UserMessage(
        session_id="test_session_id",
        content="首先我需要对《三国演义》中的关系进行建模，然后我会给你《三国演义》的部分文档，你需要把数据导入到图数据库中。最后基于构建好的图数据库，我希望了解曹操的故事以及影响力。",
        context="《三国演义》中的曹操是一个充满争议的历史人物。他既是一个雄才大略的枭雄，也是一个爱才惜才的领袖；既是一个残暴的统治者，也是一个浪漫的诗人。通过图谱分析，我们将从数据的角度来解读这位复杂的历史人物。",
    )

    await agentic_service.execute(user_message=user_message)

    while 1:
        result = await agentic_service.query_result(session_id="test_session_id")
        print(result)
        # sleep for 5 seconds
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
