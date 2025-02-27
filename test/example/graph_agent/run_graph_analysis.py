from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


def main():
    """Main function"""
    mas = AgenticService.load("test/example/graph_agent/graph_analysis.yml")
    user_message = TextMessage(
        payload="用户目前的需求是想知道在当前图数据库中，影响力最大的节点是哪个？我需要通过执行算法来找到这个节点。",
        assigned_expert_name="Graph Analysis Expert",
    )
    service_message = mas.execute(message=user_message)
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    main()
