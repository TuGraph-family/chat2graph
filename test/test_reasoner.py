from typing import Tuple
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.adpter.dbgpt_agent_adapter import DBGPTAgentAdapter
from app.agent.reasoner.dual_llm import DualLLMReasoner
from app.memory.message import AgentMessage


@pytest.fixture
async def mock_agents():
    """Fixture to provide mocked actor and thinker agents."""
    with patch(
        "app.agent.adpter.agent_adpter_factory.AgentAdapterFactory.create",
        new_callable=AsyncMock,
    ) as mock_create:
        # Create mock agents
        mock_actor = AsyncMock(spec=DBGPTAgentAdapter)
        mock_thinker = AsyncMock(spec=DBGPTAgentAdapter)

        # Configure mock_create to return different agents based on name
        async def side_effect(**kwargs):
            if kwargs.get("name") == "Actor":
                return mock_actor
            return mock_thinker

        mock_create.side_effect = side_effect
        yield mock_actor, mock_thinker


@pytest.mark.asyncio
async def test_dual_llm_reasoner_creation():
    """Test DualLLMReasoner creation."""
    task = "Tell me a joke."
    reasoner = await DualLLMReasoner.create(task=task)

    assert isinstance(reasoner, DualLLMReasoner)
    assert reasoner.task == task
    assert reasoner._initialized is True


@pytest.mark.asyncio
async def test_dual_llm_reasoner_inference(mock_agents: Tuple[AsyncMock, AsyncMock]):
    """Test DualLLMReasoner inference process."""
    mock_actor, mock_thinker = mock_agents

    # Mock response messages
    thinker_response = AgentMessage(
        msg_id="2",
        sender_id="Thinker AI",
        receiver_id="Actor AI",
        status="completed",
        content=(
            "Judgement: None\n"
            "Instruction: Tell a short knock-knock joke\n"
            "Input: Make it funny and appropriate"
        ),
        timestamp="2024-01-01",
    )

    actor_response = AgentMessage(
        msg_id="3",
        sender_id="Actor AI",
        receiver_id="Thinker AI",
        status="completed",
        content=(
            "Thought: I'll tell a classic knock-knock joke\n"
            "Action: Telling joke\n"
            "Feedback: Knock knock! Who's there? Interrupting cow. Interrupting cow w- MOO!\n"
            "TASK_DONE"
        ),
        timestamp="2024-01-01",
    )

    # Set up mock responses
    mock_thinker.receive_message.return_value = thinker_response
    mock_actor.receive_message.return_value = actor_response

    # Create and test reasoner
    task = "Tell me a joke."
    reasoner = await DualLLMReasoner.create(task=task)
    await reasoner.infer(reasoning_rounds=1)

    # Verify the interactions
    assert mock_thinker.receive_message.called
    assert mock_actor.receive_message.called

    # Verify message flow
    messages = reasoner.memory.get_messages()
    assert len(messages) == 2  # Should have both thinker and actor messages
    assert messages[0].sender_id == "Thinker AI"
    assert messages[1].sender_id == "Actor AI"
    assert "TASK_DONE" in messages[1].content


@pytest.mark.asyncio
async def test_dual_llm_reasoner_multiple_rounds(
    mock_agents: Tuple[AsyncMock, AsyncMock],
):
    """Test DualLLMReasoner with multiple reasoning rounds."""
    mock_actor, mock_thinker = mock_agents

    # Mock responses without TASK_DONE first, then with TASK_DONE
    responses_without_done = AgentMessage(
        msg_id="2",
        sender_id="Actor AI",
        receiver_id="Thinker AI",
        status="completed",
        content="Thought: Need more thinking\nAction: Continue\nFeedback: None",
        timestamp="2024-01-01",
    )

    response_with_done = AgentMessage(
        msg_id="3",
        sender_id="Actor AI",
        receiver_id="Thinker AI",
        status="completed",
        content="Thought: Task complete\nAction: None\nFeedback: None\nTASK_DONE",
        timestamp="2024-01-01",
    )

    # Set up mock to return different responses for first and second calls
    mock_actor.receive_message.side_effect = [
        responses_without_done,
        response_with_done,
    ]
    mock_thinker.receive_message.return_value = responses_without_done

    # Create and test reasoner
    task = "Tell me a joke."
    reasoner = await DualLLMReasoner.create(task=task)
    await reasoner.infer(reasoning_rounds=3)  # Set higher than actual rounds needed

    # Verify number of interactions
    assert mock_actor.receive_message.call_count == 2  # Should stop after TASK_DONE
    assert mock_thinker.receive_message.call_count == 2


@pytest.mark.asyncio
async def test_dual_llm_reasoner_initialization_error():
    """Test DualLLMReasoner initialization error handling."""
    with patch(
        "app.agent.adpter.agent_adpter_factory.AgentAdapterFactory.create",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.side_effect = Exception("Initialization error")

        with pytest.raises(Exception) as exc_info:
            await DualLLMReasoner.create(task="Test task")

        assert str(exc_info.value) == "Initialization error"
