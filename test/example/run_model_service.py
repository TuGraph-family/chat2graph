import asyncio
from typing import List

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory


async def main():
    """Main function."""
    # create model service using factory method
    model_service = ModelServiceFactory.create(model_platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
    job_id: str = "test_job_id"

    # create test messages
    messages: List[ModelMessage] = [
        ModelMessage(
            id="1",
            source_type=MessageSourceType.THINKER,
            payload="Hello, how are you? I am Alice.",
            job_id=job_id,
            step=1,
        ),
        ModelMessage(
            id="2",
            source_type=MessageSourceType.ACTOR,
            payload="I'm fine, thank you.",
            job_id=job_id,
            step=2,
        ),
        ModelMessage(
            id="3",
            source_type=MessageSourceType.THINKER,
            payload="What's my name?",
            job_id=job_id,
            step=3,
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
