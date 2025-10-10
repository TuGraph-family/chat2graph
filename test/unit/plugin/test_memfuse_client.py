from typing import Any, Dict, List

import pytest

from app.core.common.system_env import SystemEnv
from app.core.model.message import ModelMessage
from app.core.model.task import MemoryKey
from app.core.sdk.init_server import init_server
from app.plugin.memfuse.operator_memory import MemFuseOperatorMemory
from app.plugin.memfuse.reasoner_memory import MemFuseReasonerMemory

init_server()


class DummyMem:
    """A dummy MemFuse client for testing."""
    def __init__(self, results: List[Any] | None = None, raise_on: str | None = None):
        self._results = results or []
        self._raise_on = raise_on
        self.add_calls: List[Dict[str, Any]] = []

    async def query(self, *args, **kwargs):
        """Query method that can raise or return preset results."""
        if self._raise_on == "query":
            raise RuntimeError("query failed")
        return {"data": {"results": self._results}}

    async def add(self, messages, metadata=None):
        """Add method that can raise or return preset results."""
        if self._raise_on == "add":
            raise RuntimeError("add failed")
        self.add_calls.append({"messages": messages, "metadata": metadata})
        return {"status": "success"}


@pytest.mark.asyncio
async def test_reasoner_retrieve_success(monkeypatch):
    """Test successful retrieval with various result formats."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseReasonerMemory(job_id="job_x", operator_id="op_1")

    dummy = DummyMem(
        results=[
            "raw string result",
            {"content": "from content"},
            {"text": "from text"},
            {"snippet": "from snippet"},
            {"unknown": 123},
        ]
    )
    mem._memory = dummy

    out = mem.retrieve(MemoryKey(job_id="job_x", operator_id="op_1"), "hello")
    assert len(out) == 1
    content = out[0].content
    assert "raw string result" in content
    assert "from content" in content
    assert "from text" in content
    assert "from snippet" in content
    assert "unknown" in content


def test_reasoner_retrieve_failure_raises_runtime_error(monkeypatch):
    """Test that retrieval errors are handled gracefully and return empty list."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseReasonerMemory(job_id="job_y", operator_id="op_2")

    dummy = DummyMem(raise_on="query")
    mem._memory = dummy
    with pytest.raises(RuntimeError):
        mem.retrieve(MemoryKey(job_id="job_y", operator_id="op_2"), "hello")


def test_reasoner_retrieve_sync_without_event_loop(monkeypatch):
    """Test that retrieve works in sync context when no event loop is running."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseReasonerMemory(job_id="job_z", operator_id="op_3")

    dummy = DummyMem(results=["a", "b"])
    mem._memory = dummy

    out = mem.retrieve(MemoryKey(job_id="job_z", operator_id="op_3"), "hello")
    assert len(out) == 1
    assert "a" in out[0].content
    assert "b" in out[0].content


def test_reasoner_memorize_includes_metadata(monkeypatch):
    """Test successful memorize with metadata."""
    SystemEnv.ENABLE_MEMFUSE = True
    SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH = 50
    mem = MemFuseReasonerMemory(job_id="job_meta", operator_id="op_meta")

    dummy = DummyMem()
    mem._memory = dummy

    reasoner_messages = [ModelMessage(payload="hi", job_id="job_meta", step=1)]
    mem.memorize(MemoryKey(job_id="job_meta", operator_id="op_meta"), "sys", "result")

    assert len(dummy.add_calls) == 1
    call = dummy.add_calls[0]
    # The metadata is now added to each message, not as a separate argument
    assert call["messages"][0]["metadata"] == {"task_eos": True}
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "assistant"


def test_reasoner_memorize_failure_raises_runtime_error(monkeypatch):
    """Test that memorize errors are handled gracefully and do not raise."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseReasonerMemory(job_id="job_err", operator_id="op_err")

    dummy = DummyMem(raise_on="add")
    mem._memory = dummy

    with pytest.raises(RuntimeError):
        mem.memorize(MemoryKey(job_id="job_err", operator_id="op_err"), "sys", "result")

# ---- Operator Memory ----
@pytest.mark.asyncio
async def test_operator_memory_retrieve_success(monkeypatch):
    """Test successful retrieval with various result formats."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseOperatorMemory(job_id="job_x", operator_id="op_1")

    dummy = DummyMem(
        results=[
            "raw string result",
            {"content": "from content"},
            {"text": "from text"},
            {"snippet": "from snippet"},
            {"unknown": 123},
        ]
    )
    mem._memory = dummy

    out = mem.retrieve(MemoryKey(job_id="job_x", operator_id="op_1"), "hello")
    assert len(out) == 1
    content = out[0].content
    assert "raw string result" in content
    assert "from content" in content
    assert "from text" in content
    assert "from snippet" in content
    assert "unknown" in content


def test_operator_memory_retrieve_failure_raises_runtime_error(monkeypatch):
    """Test that retrieval errors are handled gracefully and return empty list."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseOperatorMemory(job_id="job_y", operator_id="op_2")

    dummy = DummyMem(raise_on="query")
    mem._memory = dummy
    with pytest.raises(RuntimeError):
        mem.retrieve(MemoryKey(job_id="job_y", operator_id="op_2"), "hello")


def test_operator_memory_retrieve_sync_without_event_loop(monkeypatch):
    """Test that retrieve works in sync context when no event loop is running."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseOperatorMemory(job_id="job_z", operator_id="op_3")

    dummy = DummyMem(results=["a", "b"])
    mem._memory = dummy

    out = mem.retrieve(MemoryKey(job_id="job_z", operator_id="op_3"), "hello")
    assert len(out) == 1
    assert "a" in out[0].content
    assert "b" in out[0].content


def test_operator_memory_memorize_includes_metadata(monkeypatch):
    """Test successful memorize with metadata."""
    SystemEnv.ENABLE_MEMFUSE = True
    SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH = 50
    mem = MemFuseOperatorMemory(job_id="job_meta", operator_id="op_meta")

    dummy = DummyMem()
    mem._memory = dummy

    mem.memorize(MemoryKey(job_id="job_meta", operator_id="op_meta"), "some_input", "result")

    assert len(dummy.add_calls) == 1
    call = dummy.add_calls[0]
    # The metadata is now added to each message, not as a separate argument
    assert call["messages"][0]["metadata"] == {"task_eos": True}
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "assistant"


def test_operator_memory_memorize_failure_raises_runtime_error(monkeypatch):
    """Test that memorize errors are handled gracefully and do not raise."""
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseOperatorMemory(job_id="job_err", operator_id="op_err")

    dummy = DummyMem(raise_on="add")
    mem._memory = dummy

    with pytest.raises(RuntimeError):
        mem.memorize(MemoryKey(job_id="job_err", operator_id="op_err"), "some_input", "result")
        mem.memorize(MemoryKey(job_id="job_err", operator_id="op_err"), "some_input", "result")
