import asyncio
import time
from typing import List

from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.commom.type import MessageSourceType, PlatformType
from app.memory.message import ModelMessage


async def main():
    """Main function."""
    # create model service using factory method
    model_service = ModelServiceFactory.create(platform_type=PlatformType.DBGPT)

    # create test messages
    messages: List[ModelMessage] = [
        ModelMessage(
            id="1",
            source_type=MessageSourceType.THINKER,
            content="Hello, how are you? I am Alice.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        ModelMessage(
            id="2",
            source_type=MessageSourceType.ACTOR,
            content="I'm fine, thank you.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        ModelMessage(
            id="3",
            source_type=MessageSourceType.THINKER,
            content="What's my name?",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
    ]

    # generate response
    response: ModelMessage = await model_service.generate(
        sys_prompt="test_sys_prompt", messages=messages
    )
    print("Generated response:\n", response.get_payload())
    assert "Alice" in response.get_payload()


if __name__ == "__main__":
    asyncio.run(main())
