import time
from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from app.agent.reasoner.dual_model import DualModelReasoner
from app.agent.reasoner.model_config import ModelConfig
from app.memory.memory import BuiltinMemory
from app.memory.message import AgentMessage


@pytest.fixture
async def dual_reasoner():
    """Fixture to create a DualModelReasoner with mocked generate methods."""
    model_config = ModelConfig()
    reasoner = DualModelReasoner(model_config=model_config)

    # create default response for generate
    actor_default_response = AgentMessage(
        sender_id="Actor",
        receiver_id="Thinker",
        content="Action: FINISH\nFeedback: Task completed successfully",
        status="successed",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        reasoning_id="test_op",
    )
    thinker_default_response = AgentMessage(
        sender_id="Thinker",
        receiver_id="Actor",
        content="Action: FINISH\nFeedback: Task completed successfully",
        status="successed",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        reasoning_id="test_op",
    )

    # mock generate methods of both models
    reasoner._actor_model.generate = AsyncMock(return_value=actor_default_response)
    reasoner._thinker_model.generate = AsyncMock(return_value=thinker_default_response)

    return reasoner


@pytest.mark.asyncio
async def test_infer_basic_functionality(dual_reasoner: DualModelReasoner):
    """Test basic functionality of infer method."""
    test_task = "Test task description"
    test_reasoning_id = "test_op"

    result = await dual_reasoner.infer(
        reasoning_id=test_reasoning_id,
        task=test_task,
        reasoning_rounds=2,
        print_messages=False,
    )

    assert test_reasoning_id in dual_reasoner._memories
    assert isinstance(dual_reasoner._memories[test_reasoning_id], BuiltinMemory)

    messages = dual_reasoner._memories[test_reasoning_id].get_messages()
    assert len(messages) > 0
    assert messages[0].sender_id == "Actor"
    assert messages[0].receiver_id == "Thinker"

    assert dual_reasoner._thinker_model.generate.call_count == 2
    assert dual_reasoner._actor_model.generate.call_count == 2

    assert result is not None and "TASK_DONE" not in result


@pytest.mark.asyncio
async def test_infer_early_stop(dual_reasoner: DualModelReasoner):
    """Test that infer stops when stop condition is met."""
    test_reasoning_id = "test_op"

    # set specific response for early stop
    early_stop_response = AgentMessage(
        sender_id="Actor",
        receiver_id="Thinker",
        content="Action: FINISH\nFeedback: Early stop",
        status="successed",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        reasoning_id=test_reasoning_id,
    )
    dual_reasoner._actor_model.generate.return_value = early_stop_response

    with patch.object(dual_reasoner, "stop", return_value=True):
        await dual_reasoner.infer(
            reasoning_id=test_reasoning_id,
            task="Test task",
            reasoning_rounds=5,
            print_messages=False,
        )

    assert dual_reasoner._thinker_model.generate.call_count == 1
    assert dual_reasoner._actor_model.generate.call_count == 1


@pytest.mark.asyncio
async def test_infer_multiple_rounds(dual_reasoner: DualModelReasoner):
    """Test multiple rounds of inference."""
    test_reasoning_id = "test_op"

    # create response generator
    round_responses = {}

    async def mock_generate(messages: List[AgentMessage]):
        msg_count = len(round_responses)
        round_responses[msg_count] = True
        return AgentMessage(
            sender_id="Actor",
            receiver_id="Thinker",
            content=f"Round {msg_count} message",
            status="successed",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            reasoning_id=test_reasoning_id,
        )

    dual_reasoner._actor_model.generate = AsyncMock(side_effect=mock_generate)
    dual_reasoner._thinker_model.generate = AsyncMock(side_effect=mock_generate)

    # Mock stop after 3 rounds
    stop_calls = []

    def mock_stop(msg):
        stop_calls.append(msg)
        return len(stop_calls) >= 3

    with patch.object(dual_reasoner, "stop", side_effect=mock_stop):
        await dual_reasoner.infer(
            reasoning_id=test_reasoning_id,
            task="Test task",
            reasoning_rounds=5,
            print_messages=False,
        )

    messages = dual_reasoner._memories[test_reasoning_id].get_messages()
    assert len(messages) == 7  # initial + (3 rounds * 2 messages per round)


@pytest.mark.asyncio
async def test_infer_message_accumulation(dual_reasoner: DualModelReasoner):
    """Test that messages are properly accumulated in memory."""
    test_reasoning_id = "test_op"

    async def actor_generate(messages: List[AgentMessage]):
        return AgentMessage(
            sender_id="Actor",
            receiver_id="Thinker",
            content="Actor message",
            status="successed",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            reasoning_id=test_reasoning_id,
        )

    async def thinker_generate(messages: List[AgentMessage]):
        return AgentMessage(
            sender_id="Thinker",
            receiver_id="Actor",
            content="Thinker message",
            status="successed",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            reasoning_id=test_reasoning_id,
        )

    dual_reasoner._actor_model.generate = AsyncMock(side_effect=actor_generate)
    dual_reasoner._thinker_model.generate = AsyncMock(side_effect=thinker_generate)

    with patch.object(dual_reasoner, "stop", side_effect=[False, True]):
        await dual_reasoner.infer(
            reasoning_id=test_reasoning_id,
            task="Test task",
            reasoning_rounds=5,
            print_messages=False,
        )

    messages = dual_reasoner._memories[test_reasoning_id].get_messages()
    assert len(messages) == 5

    assert messages[0].sender_id == "Actor"  # initial
    assert messages[1].sender_id == "Thinker"  # first round - thinker
    assert messages[2].sender_id == "Actor"  # First round - actor
    assert messages[3].sender_id == "Thinker"  # second round - thinker
    assert messages[4].sender_id == "Actor"  # second round - actor
