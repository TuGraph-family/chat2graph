import pytest

from app.core.common.system_env import SystemEnv
from app.core.memory.memfuse_memory import MemFuseMemory
from app.core.memory.reasoner_memory import BuiltinReasonerMemory
from app.core.model.message import ModelMessage


def test_builtin_reasoner_memory_basic_ops():
    mem = BuiltinReasonerMemory()
    m1 = ModelMessage(payload="a", job_id="job", step=1)
    mem.add_message(m1)
    assert mem.get_messages() == [m1]
    assert mem.get_message_by_index(0) is m1
    assert mem.get_message_by_id(m1.get_id()) is m1

    m2 = ModelMessage(payload="b", job_id="job", step=2)
    mem.upsert_message(0, m2)
    assert mem.get_message_by_index(0) is m2
    mem.remove_message()
    assert mem.get_messages() == []
    mem.clear_messages()
    assert mem.get_messages() == []

    # external hooks are no-ops
    assert mem.retrieve("q", 3) == []
    assert mem.write_turn("sys", [], "job", "op") is None


def test_memfuse_memory_local_history_only():
    mem = MemFuseMemory(job_id="job", operator_id="op")
    m1 = ModelMessage(payload="hello", job_id="job", step=1)
    mem.add_message(m1)
    assert mem.get_messages()[0].get_payload() == "hello"


def test_to_openai_messages_truncation():
    SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH = 10
    mem = MemFuseMemory(job_id="job", operator_id="op")

    sys_prompt = "X" * 50
    msgs = [ModelMessage(payload=("Y" * 50), job_id="job", step=1)]
    out = mem._to_openai_messages(sys_prompt, msgs)

    assert out[0]["role"] == "system"
    assert out[1]["role"] == "assistant"
    assert out[0]["content"].endswith("...")
    assert out[1]["content"].endswith("...")

