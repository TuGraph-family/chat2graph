from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


def main():
    """Main function"""
    mas = AgenticService.load("test/example/graph_agent/graph_modeling.yml")
    user_message = TextMessage(
        payload="目前的问题的背景是，通过函数读取文档第50章节的内容，生成知识图谱图数据库的模式"
        "（Graph schema/label），最后调用相关函数来帮助在图数据库中创建 labels。"
        "文档的主题是三国演义。可能需要调用相关的工具（通过函数调用）来操作图数据库。",
        assigned_expert_name="Graph Modeling Expert",
    )
    service_message = mas.execute(message=user_message)
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    main()
