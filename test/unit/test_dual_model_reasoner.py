import time
from typing import List
from unittest.mock import AsyncMock

import pytest

from app.core.model.job import SubJob
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.model.task import Task
from app.core.workflow.operator_config import OperatorConfig
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.toolkit.tool import Tool


@pytest.fixture
async def mock_reasoner() -> DualModelReasoner:
    """Create a DualModelReasoner with mocked model responses."""
    reasoner = DualModelReasoner()

    actor_response = ModelMessage(
        source_type=MessageSourceType.ACTOR,
        payload="<scratchpad>\nTesting\n</scratchpad>\n<action>\nProceed\n</action>\n<feedback>\nSuccess\n</feedback>",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    thinker_response = ModelMessage(
        source_type=MessageSourceType.THINKER,
        payload="<instruction>\nTest instruction\n</instruction>\n<input>\nTest input\n</input>",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    reasoner._actor_model.generate = AsyncMock(return_value=actor_response)
    reasoner._thinker_model.generate = AsyncMock(return_value=thinker_response)

    return reasoner


@pytest.fixture
def task():
    """Create a test Task for testing."""
    job = SubJob(session_id="test_session_id", goal="Test goal")
    config = OperatorConfig(instruction="Test instruction", actions=[])
    return Task(job=job, operator_config=config)


@pytest.mark.asyncio
async def test_infer_basic_flow(mock_reasoner: DualModelReasoner, task: Task):
    """Test basic inference flow with memory management."""
    # run inference
    _ = await mock_reasoner.infer(task=task)

    # verify model interactions
    assert mock_reasoner._actor_model.generate.called
    assert mock_reasoner._thinker_model.generate.called

    # verify memory management
    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()

    # check initial message
    assert messages[0].get_source_type() == MessageSourceType.ACTOR
    assert "<scratchpad>\nEmpty" in messages[0].get_payload()

    # check message flow
    assert len(messages) > 2  # Should have initial + at least one round of interaction


@pytest.mark.asyncio
async def test_infer_early_stop(mock_reasoner: DualModelReasoner, task: Task):
    """Test inference with early stop condition."""
    # modify actor response to trigger stop condition
    stop_response = ModelMessage(
        source_type=MessageSourceType.ACTOR,
        payload="<scratchpad>\nDone\n</scratchpad>\n<action>\nStop\n</action>\n<feedback>\n<DELIVERABLE></DELIVERABLE>\n</feedback>",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    mock_reasoner._thinker_model.generate = AsyncMock(return_value=stop_response)
    mock_reasoner._actor_model.generate = AsyncMock(return_value=stop_response)

    _ = await mock_reasoner.infer(task=task)

    # verify early stop
    assert mock_reasoner._thinker_model.generate.call_count == 1
    assert mock_reasoner._actor_model.generate.call_count == 1


@pytest.mark.asyncio
async def test_infer_multiple_rounds(mock_reasoner: DualModelReasoner, task: Task):
    """Test multiple rounds of inference with message accumulation."""
    round_count = 0

    async def generate_with_rounds(
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: List[Tool] | None = None,
    ) -> ModelMessage:
        nonlocal round_count
        round_count += 1
        return ModelMessage(
            source_type=MessageSourceType.ACTOR
            if round_count % 2 == 0
            else MessageSourceType.THINKER,
            payload=f"Round {round_count} content",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    # set both models to use round-based generation
    mock_reasoner._actor_model.generate = AsyncMock(side_effect=generate_with_rounds)
    mock_reasoner._thinker_model.generate = AsyncMock(side_effect=generate_with_rounds)

    _ = await mock_reasoner.infer(task=task)

    # verify message accumulation
    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()

    assert len(messages) > round_count  # Including initial message

    for i in range(1, len(messages) - 1, 2):
        assert messages[i].get_source_type() == MessageSourceType.THINKER
        assert messages[i + 1].get_source_type() == MessageSourceType.ACTOR


@pytest.mark.asyncio
async def test_infer_error_handling(mock_reasoner: DualModelReasoner, task: Task):
    """Test inference error handling."""
    # simulate model generation error
    mock_reasoner._thinker_model.generate = AsyncMock(side_effect=Exception("Model error"))

    with pytest.raises(Exception) as exc_info:
        await mock_reasoner.infer(task=task)

    assert str(exc_info.value) == "Model error"

    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()
    assert len(messages) == 1
    assert messages[0].get_source_type() == MessageSourceType.ACTOR


@pytest.mark.asyncio
async def test_infer_without_operator(mock_reasoner: DualModelReasoner, task: Task):
    """Test inference without caller (using temporary memory)."""
    task.operator_config = None
    _ = await mock_reasoner.infer(task=task)

    assert mock_reasoner._thinker_model.generate.called
    assert mock_reasoner._actor_model.generate.called

    # since there is no operator, the reasoner will not persist the memory
    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()
    assert not messages
