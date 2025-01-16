import time
from unittest.mock import AsyncMock

import pytest

from app.agent.job import Job
from app.agent.reasoner.mono_model_reasoner import MonoModelReasoner
from app.agent.reasoner.task import Task
from app.agent.workflow.operator.operator_config import OperatorConfig
from app.common.type import MessageSourceType
from app.memory.message import ModelMessage


@pytest.fixture
def task():
    """Create a test Task for testing."""
    job = Job(session_id="test_session_id", goal="Test goal")
    config = OperatorConfig(instruction="Test instruction", actions=[])
    return Task(job=job, operator_config=config)


@pytest.fixture
async def mock_reasoner() -> MonoModelReasoner:
    """Create a MonoModelReasoner with mocked model responses."""
    reasoner = MonoModelReasoner()

    response = ModelMessage(
        source_type=MessageSourceType.ACTOR,
        content="<scratchpad>\nTesting\n</scratchpad>\n<action>\nProceed\n</action>\n<feedback>\nSuccess\n</feedback>",
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    reasoner._model.generate = AsyncMock(return_value=response)

    return reasoner


@pytest.mark.asyncio
async def test_infer_basic_flow(mock_reasoner: MonoModelReasoner, task: Task):
    """Test basic inference flow with memory management."""
    # run inference
    _ = await mock_reasoner.infer(task=task)

    # verify model interactions
    assert mock_reasoner._model.generate.called

    # verify memory management
    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()

    # check initial message
    assert messages[0].get_source_type() == MessageSourceType.MODEL
    assert "<scratchpad>\nEmpty" in messages[0].get_payload()

    # check message flow
    assert len(messages) == 2


@pytest.mark.asyncio
async def test_infer_error_handling(mock_reasoner: MonoModelReasoner, task: Task):
    """Test inference error handling."""
    # simulate model generation error
    mock_reasoner._model.generate = AsyncMock(side_effect=Exception("Model error"))

    with pytest.raises(Exception) as exc_info:
        await mock_reasoner.infer(task=task)

    assert str(exc_info.value) == "Model error"

    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()
    assert len(messages) == 1
    assert messages[0].get_source_type() == MessageSourceType.MODEL


@pytest.mark.asyncio
async def test_infer_without_operator(mock_reasoner: MonoModelReasoner, task: Task):
    """Test inference without caller (using temporary memory)."""
    task.operator_config = None
    _ = await mock_reasoner.infer(task=task)

    assert mock_reasoner._model.generate.called

    # since there is no operator, the reasoner will not persist the memory
    reasoner_memory = mock_reasoner.get_memory(task=task)
    messages = reasoner_memory.get_messages()
    assert not messages
