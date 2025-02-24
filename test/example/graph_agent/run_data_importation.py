import asyncio

from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


async def main():
    """Main function to run the data import."""
    mas = AgenticService.load("test/example/graph_agent/data_importation.yml")

    user_message = TextMessage(
        payload="目前我们的问题的背景是，通过函数读取文档的内容，结合当前图数据库中的图模型完成实体和关系的数据抽取和数据的导入，并输出导入结果。"
        "你至少需要导入 100 个数据点。",
        assigned_expert_name="Data Importation Expert",
    )
    service_message = await mas.execute(message=user_message)
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
