from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


def main():
    """Main function"""
    mas = AgenticService.load("test/example/graph_agent/graph_modeling.yml")
    user_message = TextMessage(
        payload="查询节点，vertex_type为entity，查询条件为节点的属性description包含'github用户'"
        "图数据库的主题是TuGraph。可能需要调用相关的工具（通过函数调用）来操作图数据库。",
        assigned_expert_name="Query Expert",
    )
    service_message = mas.execute(message=user_message)
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    main()
