import pytest

from app.core.common.system_env import SystemEnv
from app.core.memory.memory import BuiltinMemory
from app.core.model.message import ModelMessage
from app.core.model.task import MemoryKey
from app.core.sdk.init_server import init_server
from app.plugin.memfuse.operator_memory import MemFuseOperatorMemory
from app.plugin.memfuse.reasoner_memory import MemFuseReasonerMemory

init_server()


@pytest.mark.asyncio
async def test_builtin_reasoner_memory_basic_ops():
    """Test basic operations of BuiltinMemory."""
    mem = BuiltinMemory()
    m1 = ModelMessage(payload="a", job_id="job", step=1)
    mem.add_message(m1)
    assert mem.get_messages() == [m1]
    assert mem.get_message_by_index(0) is m1
    assert mem.get_message_by_id(m1.get_id()) is m1

    m2 = ModelMessage(payload="b", job_id="job", step=2)
    mem.upsert_message(0, m2)
    assert mem.get_message_by_index(0) is m2
    mem.remove_message()
    assert not mem.get_messages()
    mem.clear_messages()
    assert not mem.get_messages()

    # external hooks are no-ops
    assert not await mem.retrieve(
        MemoryKey(
            job_id="test_job_id",
            operator_id="test_operator_id",
        ),
        "q",
    )
    assert (
        await mem.memorize(
            MemoryKey(job_id="test_job_id", operator_id="test_operator_id"),
            "sys",
            "job_result",
        )
        is None
    )


def test_memfuse_memory_local_history_only():
    """Test MemFuseReasonerMemory basic operations with local history only."""
    reasoner_mem = MemFuseReasonerMemory(job_id="job", operator_id="op")
    m1 = ModelMessage(payload="hello", job_id="job", step=1)
    reasoner_mem.add_message(m1)
    assert reasoner_mem.get_messages()[0].get_payload() == "hello"

    operator_mem = MemFuseOperatorMemory(job_id="job", operator_id="op")
    m2 = ModelMessage(payload="world", job_id="job", step=1)
    operator_mem.add_message(m2)
    assert operator_mem.get_messages()[0].get_payload() == "world"


@pytest.mark.asyncio
def test_to_openai_messages_truncation():
    """Test _to_openai_messages with truncation."""
    SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH = 10
    mem = MemFuseReasonerMemory(job_id="job", operator_id="op")

    sys_prompt = "X" * 50
    msgs = [ModelMessage(payload=("Y" * 50), job_id="job", step=1)]
    out = mem._to_openai_messages(sys_prompt, msgs)

    assert out[0]["role"] == "system"
    assert out[1]["role"] == "assistant"
    assert out[0]["content"].endswith("...")
    assert out[1]["content"].endswith("...")
