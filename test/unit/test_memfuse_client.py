import asyncio
from typing import Any, Dict, List

import pytest

from app.core.common.system_env import SystemEnv
from app.core.memory.memfuse_memory import MemFuseMemory
from app.core.model.message import ModelMessage


class DummyMem:
    def __init__(self, results: List[Any] | None = None, raise_on: str | None = None):
        self._results = results or []
        self._raise_on = raise_on
        self.add_calls: List[Dict[str, Any]] = []

    async def query(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        if self._raise_on == "query":
            raise RuntimeError("query failed")
        return {"data": {"results": self._results}}

    async def add(self, messages, metadata=None):  # type: ignore[no-untyped-def]
        if self._raise_on == "add":
            raise RuntimeError("add failed")
        self.add_calls.append({"messages": messages, "metadata": metadata})
        return {"status": "success"}


@pytest.mark.asyncio
async def test_aretrieve_success(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseMemory(job_id="job_x", operator_id="op_1")

    dummy = DummyMem(results=[
        "raw string result",
        {"content": "from content"},
        {"text": "from text"},
        {"snippet": "from snippet"},
        {"unknown": 123},
    ])

    async def fake_ctx(self):  # type: ignore[no-redef]
        return dummy

    monkeypatch.setattr(MemFuseMemory, "_ensure_context", fake_ctx)

    out = await mem.aretrieve("hello", top_k=3)
    # unknown dict becomes stringified, 5 items expected
    assert out[0] == "raw string result"
    assert "from content" in out
    assert "from text" in out
    assert "from snippet" in out
    assert any("unknown" in s for s in out)


@pytest.mark.asyncio
async def test_aretrieve_error_returns_empty(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseMemory(job_id="job_y", operator_id="op_2")

    dummy = DummyMem(raise_on="query")

    async def fake_ctx(self):  # type: ignore[no-redef]
        return dummy

    monkeypatch.setattr(MemFuseMemory, "_ensure_context", fake_ctx)

    out = await mem.aretrieve("hello", top_k=3)
    assert out == []


def test_retrieve_sync_executes_when_no_loop(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseMemory(job_id="job_z", operator_id="op_3")

    dummy = DummyMem(results=["a", "b"]) 

    async def fake_ctx(self):  # type: ignore[no-redef]
        return dummy

    monkeypatch.setattr(MemFuseMemory, "_ensure_context", fake_ctx)

    out = mem.retrieve("hello", top_k=2)
    assert out == ["a", "b"]


@pytest.mark.asyncio
async def test_awrite_turn_success_metadata(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH = 50
    mem = MemFuseMemory(job_id="job_meta", operator_id="op_meta")

    dummy = DummyMem()

    async def fake_ctx(self):  # type: ignore[no-redef]
        return dummy

    monkeypatch.setattr(MemFuseMemory, "_ensure_context", fake_ctx)

    msgs = [ModelMessage(payload="hi", job_id="job_meta", step=1)]
    await mem.awrite_turn("sys", msgs, job_id="job_meta", operator_id="op_meta")

    assert len(dummy.add_calls) == 1
    call = dummy.add_calls[0]
    assert call["metadata"] == {"task": "job_meta"}
    # openai messages contains system + assistant
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_awrite_turn_swallows_errors(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    mem = MemFuseMemory(job_id="job_err", operator_id="op_err")

    dummy = DummyMem(raise_on="add")

    async def fake_ctx(self):  # type: ignore[no-redef]
        return dummy

    monkeypatch.setattr(MemFuseMemory, "_ensure_context", fake_ctx)

    msgs = [ModelMessage(payload="hi", job_id="job_err", step=1)]
    await mem.awrite_turn("sys", msgs, job_id="job_err", operator_id="op_err")
    # no exception raised and no successful add recorded
    assert dummy.add_calls == []


@pytest.mark.asyncio
async def test_aretrieve_disabled_returns_empty():
    SystemEnv.ENABLE_MEMFUSE = False
    mem = MemFuseMemory(job_id="job_off", operator_id="op_off")
    out = await mem.aretrieve("anything", top_k=5)
    assert out == []
