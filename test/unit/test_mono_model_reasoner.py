from unittest.mock import AsyncMock

import pytest

from app.core.common.type import MessageSourceType
from app.core.model.job import SubJob
from app.core.model.message import ModelMessage
from app.core.model.task import Task
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.workflow.operator_config import OperatorConfig

job_id: str = "test_job_id"


@pytest.fixture
def task():
    """Create a test Task for testing."""
    job = SubJob(session_id="test_session_id", goal="Test goal")
    config = OperatorConfig(instruction="Test instruction", actions=[])
    return Task(job=job, operator_config=config)


@pytest.fixture
async def mock_reasoner() -> MonoModelReasoner:
    """Create a MonoModelReasoner with mocked model responses."""
    reasoner = MonoModelReasoner()

    response = ModelMessage(
        source_type=MessageSourceType.ACTOR,
        payload="<deep_thinking>\nTesting\n</deep_thinking>\n<action>\nProceed\n</action>",
        job_id=job_id,
        step=1,
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
    assert "<deep_thinking>" in messages[0].get_payload()

    # check message flow
    assert len(messages) >= 1


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
