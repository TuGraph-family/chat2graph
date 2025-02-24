import asyncio

from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


async def main():
    """Main function"""
    mas = AgenticService.load("test/example/graph_agent/graph_modeling.yml")
    user_message = TextMessage(
        payload="""我在执行Cypher语句
CALL db.createVertexLabelByJson('{
    "label": "州",
    "primary": "state",
    "type": "VERTEX",
    "properties": [
        {
            "name": "state",
            "type": "INT12"
        }
    ]
}');
的时候，遇到报错：执行失败 unknown keyword str: [INT12]，
请问原因是什么，该如何修改？""",
        assigned_expert_name="Question Answering Expert",
    )
    service_message = await mas.execute(message=user_message)
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    asyncio.run(main())
