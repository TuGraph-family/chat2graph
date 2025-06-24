from app.core.model.message import HybridMessage, TextMessage
from app.core.sdk.agentic_service import AgenticService


def main():
    """Main function."""
    mas = AgenticService.load("test/example/domain_expert/broswer_use_expert.yml")

    # set a question that requires web research
    user_message = TextMessage(
        payload="Investigate which public products have been open-sourced by the Ant Group's TuGraph team as of June 2025.",  # noqa: E501
    )

    # submit the job
    service_message = mas.session().submit(user_message).wait()

    # print the result
    if isinstance(service_message, TextMessage):
        print(f"Service Result:\n{service_message.get_payload()}")
    elif isinstance(service_message, HybridMessage):
        text_message = service_message.get_instruction_message()
        print(f"Service Result:\n{text_message.get_payload()}")


if __name__ == "__main__":
    main()
