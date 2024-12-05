import asyncio
import time
from typing import List

from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.commom.type import PlatformType
from app.memory.message import AgentMessage


async def main():
    """Main function."""
    # create model service using factory method
    model_service = ModelServiceFactory.create(platform_type=PlatformType.DBGPT)

    # create test messages
    messages: List[AgentMessage] = [
        AgentMessage(
            message_id="1",
            sender="Thinker",
            content="Hello, how are you? I am Alice.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        AgentMessage(
            message_id="2",
            sender="Actor",
            content="I'm fine, thank you.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        AgentMessage(
            message_id="3",
            sender="Thinker",
            content="What's my name?",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
    ]

    # generate response
    response: AgentMessage = await model_service.generate(messages)
    print("Generated response:\n", response)
    assert "Alice" in response.content


if __name__ == "__main__":
    asyncio.run(main())
