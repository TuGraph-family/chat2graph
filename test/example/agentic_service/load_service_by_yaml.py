from app.core.model.message import TextMessage
from app.core.sdk.agentic_service import AgenticService


def main():
    """Main function."""
    mas = AgenticService.load("app/core/sdk/chat2graph.yml")

    # set the user message
    user_message = TextMessage(payload="通过工具来阅读原文，我需要对《三国演义》中的关系进行建模。")

    # submit the job
    service_message = mas.session().submit(user_message).wait()

    # print the result
    print(f"Service Result:\n{service_message.get_payload()}")


if __name__ == "__main__":
    main()
