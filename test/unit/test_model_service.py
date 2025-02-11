import time
from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage


@pytest.fixture
def mock_model_service():
    """Fixture to create a mock model service."""
    with patch("app.agent.reasoner.model_service_factory.ModelServiceFactory") as mock_factory:
        # create a mock model service instance
        mock_service = AsyncMock()

        # Configure the mock to return a predefined response
        mock_response = ModelMessage(
            id="4",
            source_type=MessageSourceType.ACTOR,
            payload="Your name is Alice, as you mentioned earlier.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        mock_service.generate = AsyncMock(return_value=mock_response)

        # configure the factory to return our mock service
        mock_factory.create.return_value = mock_service

        yield mock_service


@pytest.fixture
def test_messages() -> List[ModelMessage]:
    """Fixture to create test messages."""
    return [
        ModelMessage(
            id="1",
            source_type=MessageSourceType.THINKER,
            payload="Hello, how are you? I am Alice.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        ModelMessage(
            id="2",
            source_type=MessageSourceType.ACTOR,
            payload="I'm fine, thank you.",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
        ModelMessage(
            id="3",
            source_type=MessageSourceType.THINKER,
            payload="What's my name?",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        ),
    ]


@pytest.mark.asyncio
async def test_model_service_generate(
    mock_model_service: AsyncMock, test_messages: List[ModelMessage]
):
    """Test the model service generate function."""
    # get the mock service
    model_service = mock_model_service

    # generate response using the mock service
    response = await model_service.generate(test_messages)

    # assertions
    assert response is not None
    assert isinstance(response, ModelMessage)
    assert "Alice" in response.get_payload()
    assert response.get_source_type() == MessageSourceType.ACTOR

    # verify the generate method was called with correct arguments
    model_service.generate.assert_called_once_with(test_messages)


@pytest.mark.asyncio
async def test_model_service_factory():
    """Test the model service factory creation."""
    with patch(
        "app.agent.reasoner.model_service_factory.ModelServiceFactory.create"
    ) as mock_create:
        # configure mock
        mock_service = AsyncMock()
        mock_create.return_value = mock_service

        # create service using factory
        service = ModelServiceFactory.create(platform_type=SystemEnv.PLATFORM_TYPE)

        # Assertions
        assert service is not None
        assert service == mock_service
        mock_create.assert_called_once_with(platform_type=SystemEnv.PLATFORM_TYPE)


def test_agent_message_creation():
    """Test the creation of ModelMessage objects."""
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    message = ModelMessage(
        id="test",
        source_type=MessageSourceType.THINKER,
        payload="Test message",
        timestamp=timestamp,
    )

    assert message.get_id() == "test"
    assert message.get_source_type() == MessageSourceType.THINKER
    assert message.get_payload() == "Test message"
    assert message.get_timestamp() == timestamp
