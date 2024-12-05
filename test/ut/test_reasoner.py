import time
from typing import List
from unittest.mock import AsyncMock

import pytest

from app.agent.reasoner.dual_model_reasoner import DualModelReasoner
from app.agent.reasoner.reasoner import ReasonerCaller
from app.agent.task import Task
from app.commom.type import MessageSourceType
from app.memory.message import AgentMessage


class TestCaller(ReasonerCaller):
    """Test ReasonerCaller for testing."""

    def __init__(self):
        super().__init__()
        self._id = "test_caller_id"

    def get_id(self) -> str:
        """Get the unique identifier of the caller."""
        return self._id


@pytest.fixture
def caller():
    """Create a standard ReasonerCaller for testing."""
    return TestCaller()


@pytest.fixture
async def mock_reasoner() -> DualModelReasoner:
    """Create a DualModelReasoner with mocked model responses."""
    reasoner = DualModelReasoner()

    actor_response = AgentMessage(
        source_type=MessageSourceType.ACTOR,
        content="Scratchpad: Testing\nAction: Proceed\nFeedback: Success",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    thinker_response = AgentMessage(
        source_type=MessageSourceType.THINKER,
        content="Instruction: Test instruction\nInput: Test input",
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
    task = Task(
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )

    # run inference
    _ = await mock_reasoner.infer(task=task, caller=caller)

    # verify model interactions
    assert mock_reasoner._actor_model.generate.called
    assert mock_reasoner._thinker_model.generate.called

    # verify memory management
    reasoner_memory = mock_reasoner.get_memory(task=task, caller=caller)
    messages = reasoner_memory.get_messages()

    # check initial message
    assert messages[0].get_source_type() == MessageSourceType.ACTOR
    assert "Scratchpad: Empty" in messages[0].get_payload()

    # check message flow
    assert len(messages) > 2  # Should have initial + at least one round of interaction


@pytest.mark.asyncio
async def test_infer_early_stop(
    mock_reasoner: DualModelReasoner, caller: ReasonerCaller
):
    """Test inference with early stop condition."""
    # modify actor response to trigger stop condition
    stop_response = AgentMessage(
        source_type=MessageSourceType.ACTOR,
        content="Scratchpad: Done\nAction: Complete\nFeedback: TASK_DONE",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    mock_reasoner._actor_model.generate = AsyncMock(return_value=stop_response)

    task = Task(
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )
    _ = await mock_reasoner.infer(task=task, caller=caller)

    # verify early stop
    assert mock_reasoner._actor_model.generate.call_count == 1
    assert mock_reasoner._thinker_model.generate.call_count == 1


@pytest.mark.asyncio
async def test_infer_multiple_rounds(
    mock_reasoner: DualModelReasoner, caller: ReasonerCaller
):
    """Test multiple rounds of inference with message accumulation."""
    round_count = 0

    async def generate_with_rounds(
        sys_prompt: str, messages: List[AgentMessage]
    ) -> AgentMessage:
        nonlocal round_count
        round_count += 1
        return AgentMessage(
            source_type=MessageSourceType.ACTOR
            if round_count % 2 == 0
            else MessageSourceType.THINKER,
            content=f"Round {round_count} content",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    # set both models to use round-based generation
    mock_reasoner._actor_model.generate = AsyncMock(side_effect=generate_with_rounds)
    mock_reasoner._thinker_model.generate = AsyncMock(side_effect=generate_with_rounds)

    task = Task(
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )
    _ = await mock_reasoner.infer(task=task, caller=caller)

    # verify message accumulation
    reasoner_memory = mock_reasoner.get_memory(task=task, caller=caller)
    messages = reasoner_memory.get_messages()

    assert len(messages) > round_count  # Including initial message

    for i in range(1, len(messages) - 1, 2):
        assert messages[i].get_source_type() == MessageSourceType.THINKER
        assert messages[i + 1].get_source_type() == MessageSourceType.ACTOR


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
        task = Task(
            session_id="test_session_id",
            goal="Test goal",
            context="Test context",
        )
        await mock_reasoner.infer(task=task, caller=caller)

    assert str(exc_info.value) == "Model error"

    reasoner_memory = mock_reasoner.get_memory(task=task, caller=caller)
    messages = reasoner_memory.get_messages()
    assert len(messages) == 1
    assert messages[0].get_source_type() == MessageSourceType.ACTOR


@pytest.mark.asyncio
async def test_infer_without_caller(mock_reasoner: DualModelReasoner):
    """Test inference without caller (using temporary memory)."""
    task = Task(
        session_id="test_session_id",
        goal="Test goal",
        context="Test context",
    )
    _ = await mock_reasoner.infer(task=task, caller=None)

    assert mock_reasoner._actor_model.generate.called
    assert mock_reasoner._thinker_model.generate.called

    assert len(mock_reasoner._memories) == 0
