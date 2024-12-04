import time
from typing import List
from unittest.mock import AsyncMock

import pytest

from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.reasoner import ReasonerCaller
from app.memory.message import AgentMessage


@pytest.fixture
def caller():
    """Create a standard ReasonerCaller for testing."""
    return ReasonerCaller(
        system_id="test_system",
        session_id="test_session",
        task_id="test_task",
        agent_id="test_agent",
        operator_id="test_operator",
    )


@pytest.fixture
async def mock_reasoner() -> DualModelReasoner:
    """Create a DualModelReasoner with mocked model responses."""
    reasoner = DualModelReasoner()

    actor_response = AgentMessage(
        sender_id="Actor",
        receiver_id="Thinker",
        content="Scratchpad: Testing\nAction: Proceed\nFeedback: Success",
        status="succeeded",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    thinker_response = AgentMessage(
        sender_id="Thinker",
        receiver_id="Actor",
        content="Instruction: Test instruction\nInput: Test input",
        status="succeeded",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    reasoner._actor_model.generate = AsyncMock(return_value=actor_response)
    reasoner._thinker_model.generate = AsyncMock(return_value=thinker_response)

    return reasoner


@pytest.mark.asyncio
async def test_infer_basic_flow(
    mock_reasoner: DualModelReasoner, caller: ReasonerCaller
):
    """Test basic inference flow with memory management."""
    test_input = "Test task input"

    # run inference
    _ = await mock_reasoner.infer(input=test_input, caller=caller)

    # verify model interactions
    assert mock_reasoner._actor_model.generate.called
    assert mock_reasoner._thinker_model.generate.called

    # verify memory management
    memory = mock_reasoner.get_memory(caller)
    messages = memory.get_messages()

    # check initial message
    assert messages[0].sender_id == "Actor"
    assert messages[0].receiver_id == "Thinker"
    assert "Scratchpad: Empty" in messages[0].content

    # check message flow
    assert len(messages) > 2  # Should have initial + at least one round of interaction


@pytest.mark.asyncio
async def test_infer_early_stop(
    mock_reasoner: DualModelReasoner, caller: ReasonerCaller
):
    """Test inference with early stop condition."""
    # modify actor response to trigger stop condition
    stop_response = AgentMessage(
        sender_id="Actor",
        receiver_id="Thinker",
        content="Scratchpad: Done\nAction: Complete\nFeedback: TASK_DONE",
        status="succeeded",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    mock_reasoner._actor_model.generate = AsyncMock(return_value=stop_response)

    _ = await mock_reasoner.infer(input="Test task", caller=caller)

    # verify early stop
    assert mock_reasoner._actor_model.generate.call_count == 1
    assert mock_reasoner._thinker_model.generate.call_count == 1


@pytest.mark.asyncio
async def test_infer_multiple_rounds(
    mock_reasoner: DualModelReasoner, caller: ReasonerCaller
):
    """Test multiple rounds of inference with message accumulation."""
    round_count = 0

    async def generate_with_rounds(messages: List[AgentMessage]) -> AgentMessage:
        nonlocal round_count
        round_count += 1
        return AgentMessage(
            sender_id="Actor" if round_count % 2 == 0 else "Thinker",
            receiver_id="Thinker" if round_count % 2 == 0 else "Actor",
            content=f"Round {round_count} content",
            status="succeeded",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    # set both models to use round-based generation
    mock_reasoner._actor_model.generate = AsyncMock(side_effect=generate_with_rounds)
    mock_reasoner._thinker_model.generate = AsyncMock(side_effect=generate_with_rounds)

    _ = await mock_reasoner.infer(input="Test task", caller=caller)

    # verify message accumulation
    memory = mock_reasoner.get_memory(caller)
    messages = memory.get_messages()

    assert len(messages) > round_count  # Including initial message

    for i in range(1, len(messages) - 1, 2):
        assert messages[i].sender_id == "Thinker"
        assert messages[i + 1].sender_id == "Actor"


@pytest.mark.asyncio
async def test_infer_error_handling(
    mock_reasoner: DualModelReasoner, caller: ReasonerCaller
):
    """Test inference error handling."""
    # simulate model generation error
    mock_reasoner._thinker_model.generate = AsyncMock(
        side_effect=Exception("Model error")
    )

    with pytest.raises(Exception) as exc_info:
        await mock_reasoner.infer(input="Test task", caller=caller)

    assert str(exc_info.value) == "Model error"

    memory = mock_reasoner.get_memory(caller)
    messages = memory.get_messages()
    assert len(messages) == 1
    assert messages[0].sender_id == "Actor"


@pytest.mark.asyncio
async def test_infer_without_caller(mock_reasoner: DualModelReasoner):
    """Test inference without caller (using temporary memory)."""
    _ = await mock_reasoner.infer(input="Test task", caller=None)

    assert mock_reasoner._actor_model.generate.called
    assert mock_reasoner._thinker_model.generate.called

    assert len(mock_reasoner._memories) == 0
