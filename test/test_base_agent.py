from unittest.mock import AsyncMock, patch

import pytest
from dbgpt.agent.core.memory import AgentMemory

from app.agent.base_agent import BaseAgent


@pytest.fixture
async def base_agent():
    """Create a base agent instance."""
    agent = BaseAgent(name="test_agent")
    await agent.init_client()
    return agent


@pytest.mark.asyncio
async def test_base_agent_creation(base_agent: BaseAgent):
    """Test base agent creation"""
    assert isinstance(base_agent, BaseAgent)
    assert base_agent.name == "test_agent"
    assert isinstance(base_agent.id, str)


@pytest.mark.asyncio
async def test_agent_memory_initialization(base_agent: BaseAgent):
    """Test agent memory initialization"""
    assert isinstance(base_agent.memory, AgentMemory)


@pytest.mark.asyncio
async def test_agent_message_flow(base_agent: BaseAgent):
    """Test the message flow between user and agent"""
    with patch.object(
        BaseAgent, "receive_message", new_callable=AsyncMock
    ) as mock_receive:
        # Setup mock responses
        mock_responses = [
            {
                "msg_id": "response_1",
                "sender_id": "agent_456",
                "receiver_id": "user_123",
                "status": "success",
                "content": "Hi Alice, nice to meet you!",
                "timestamp": "2024-01-01",
            },
            {
                "msg_id": "response_2",
                "sender_id": "agent_456",
                "receiver_id": "user_123",
                "status": "success",
                "content": "Your name is Alice.",
                "timestamp": "2024-01-01",
            },
        ]
        mock_receive.side_effect = mock_responses

        # First message
        message1 = {
            "msg_id": "1",
            "sender_id": "user_123",
            "receiver_id": "agent_456",
            "status": "pending",
            "content": "Hello, I am Alice.",
            "timestamp": "2024-01-01",
            "role": "user",
        }

        response1 = await base_agent.receive_message(message1)
        assert response1 == mock_responses[0]
        assert response1["content"] == "Hi Alice, nice to meet you!"

        # Second message
        message2 = {
            "msg_id": "2",
            "sender_id": "user_123",
            "receiver_id": "agent_456",
            "status": "pending",
            "content": "What is my name?",
            "timestamp": "2024-01-01",
            "role": "user",
        }

        response2 = await base_agent.receive_message(message2)
        assert response2 == mock_responses[1]
        assert response2["content"] == "Your name is Alice."

        assert mock_receive.call_count == 2


@pytest.mark.asyncio
async def test_tool_handling(base_agent: BaseAgent):
    """Test tool handling functionality"""

    async def mock_tool(**kwargs):
        return {"result": "success"}

    base_agent.tool_list = [mock_tool]

    tool_calls = [{"name": "mock_tool", "arguments": {"arg1": "value1"}}]

    results = await base_agent.handle_tool_call(tool_calls)
    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert results[0]["tool_name"] == "mock_tool"


@pytest.mark.asyncio
async def test_error_handling(base_agent: BaseAgent):
    """Test error handling in tool calls"""

    def error_tool(**kwargs):
        raise Exception("Test error")

    base_agent.tool_list = [error_tool]

    tool_calls = [{"name": "error_tool", "arguments": {}}]

    results = await base_agent.handle_tool_call(tool_calls)
    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert "Test error" in results[0]["error"]
