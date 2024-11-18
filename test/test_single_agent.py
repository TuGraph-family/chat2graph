from unittest.mock import AsyncMock, patch

import pytest

from app.agent.adpter.agent_adpter_factory import (
    AgentAdapterFactory,
    AgentFrameworkName,
)
from app.agent.adpter.dbgpt_agent_adapter import AgentAdapter, DBGPTAgentAdapter
from app.memory.message import AgentMessage


@pytest.fixture
async def dbgpt_agent_adapter():
    """Create an agent adapter."""
    adapter = await AgentAdapterFactory.create(agent_type=AgentFrameworkName.DBGPT)
    assert isinstance(adapter, DBGPTAgentAdapter)
    return adapter


@pytest.mark.asyncio
async def test_dbgpt_agent_adapter_creation(dbgpt_agent_adapter: AgentAdapter):
    """Test agent adapter creation"""
    assert isinstance(dbgpt_agent_adapter, DBGPTAgentAdapter)


@pytest.mark.asyncio
async def test_agent_message_flow(dbgpt_agent_adapter: AgentAdapter):
    """Test the message flow between user and agent"""
    # Mock the receive_message method
    with patch.object(
        DBGPTAgentAdapter, "receive_message", new_callable=AsyncMock
    ) as mock_receive:
        # Setup mock responses
        mock_responses = [
            AgentMessage(
                msg_id="response_1",
                sender_id="agent_456",
                receiver_id="user_123",
                status="completed",
                content="Hi Alice, nice to meet you!",
                timestamp="2024-01-01",
            ),
            AgentMessage(
                msg_id="response_2",
                sender_id="agent_456",
                receiver_id="user_123",
                status="completed",
                content="Your name is Alice.",
                timestamp="2024-01-01",
            ),
        ]
        mock_receive.side_effect = mock_responses

        # First message: User introduction
        message1 = AgentMessage(
            msg_id="1",
            sender_id="user_123",
            receiver_id="agent_456",
            status="pending",
            content="Hello, I am Alice.",
            timestamp="2024-01-01",
        )

        response1: AgentMessage = await dbgpt_agent_adapter.receive_message(message1)
        assert response1 == mock_responses[0]
        assert response1.content == "Hi Alice, nice to meet you!"

        # Second message: Agent asking about name
        message2 = AgentMessage(
            msg_id="2",
            sender_id="agent_456",
            receiver_id="user_123",
            status="pending",
            content="What is my name?",
            timestamp="2024-01-01",
        )

        response2: AgentMessage = await dbgpt_agent_adapter.receive_message(message2)
        assert response2 == mock_responses[1]
        assert response2.content == "Your name is Alice."

        # Verify receive_message was called exactly twice
        assert mock_receive.call_count == 2
