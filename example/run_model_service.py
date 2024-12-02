import asyncio
import os
import time
from typing import List

from app.agent.reasoner.model_config import ModelConfig
from app.agent.reasoner.model_service import ModelServiceFactory
from app.memory.message import AgentMessage
from app.type import PlatformType


async def main():
    """Main function."""
    model_config = ModelConfig(
        model_alias="qwen-max",
        api_base=os.getenv("QWEN_API_BASE"),
        api_key=os.getenv("QWEN_API_KEY"),
    )
    # create model service using factory method
    model_service = ModelServiceFactory.create(
        platform_type=PlatformType.DBGPT, model_config=model_config
    )

    # create test messages
    sender_id = "user"
    receiver_id = "assistant"
    messages: List[AgentMessage] = [
        AgentMessage(
            msg_id="1",
            sender_id=sender_id,
            receiver_id=receiver_id,
            status="successed",
            content="Hello, how are you? I am Alice.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        AgentMessage(
            msg_id="2",
            sender_id=receiver_id,
            receiver_id=sender_id,
            status="successed",
            content="I'm fine, thank you.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        AgentMessage(
            msg_id="3",
            sender_id=sender_id,
            receiver_id=receiver_id,
            status="successed",
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
