import pytest

from app.core.common.system_env import SystemEnv
from app.core.memory.enhanced.hook import MemFuseReasonerHook
from app.core.model.job import Job
from app.core.model.message import ModelMessage
from app.core.model.task import Task
from app.core.workflow.operator_config import OperatorConfig
from app.core.service.memory_service import MemoryService


class _StubMemory:
    def __init__(self, snippets=None):
        self._snippets = snippets or []
        self.write_calls = []

    async def aretrieve(self, query_text: str, top_k: int):  # noqa: ARG002
        return list(self._snippets)

    def write_turn(self, sys_prompt, messages, job_id, operator_id):  # noqa: ARG002
        self.write_calls.append(
            {
                "sys_prompt": sys_prompt,
                "messages": messages,
                "job_id": job_id,
                "operator_id": operator_id,
            }
        )


@pytest.mark.asyncio
async def test_pre_reasoning_injects_textinsight(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    job = Job(goal="G", context="C")
    task = Task(job=job, operator_config=OperatorConfig(instruction="I", actions=[]))

    stub = _StubMemory(["alpha", "beta"])  # expected snippets
    monkeypatch.setattr(
        MemoryService,
        "get_or_create_reasoner_memory",
        lambda self, job_id, operator_id: stub,  # noqa: ARG002
    )

    hook = MemFuseReasonerHook()
    out_task = await hook.pre_reasoning(task, reasoner=None)

    assert out_task.insights is not None
    assert len(out_task.insights) >= 1
    insight = out_task.insights[-1]
    assert "[memory]" in insight.content
    assert "alpha" in insight.content and "beta" in insight.content
    # tags include memory/memfuse and scoping ids
    assert any(t.startswith("job:") for t in insight.tags)
    assert any(t.startswith("op:") for t in insight.tags)


@pytest.mark.asyncio
async def test_post_reasoning_writes_turn(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True
    job = Job(goal="G2", context="C2")
    task = Task(job=job, operator_config=OperatorConfig(instruction="II", actions=[]))

    stub = _StubMemory()
    monkeypatch.setattr(
        MemoryService,
        "get_or_create_reasoner_memory",
        lambda self, job_id, operator_id: stub,  # noqa: ARG002
    )

    class _DummyReasoner:
        def get_memory(self, t):  # noqa: ARG002
            return type(
                "RM",
                (),
                {"get_messages": lambda self2: [ModelMessage(payload="hi", job_id=job.id, step=1)]},
            )()

    hook = MemFuseReasonerHook()
    await hook.post_reasoning(task, _DummyReasoner())

    assert len(stub.write_calls) == 1
    call = stub.write_calls[0]
    assert call["job_id"] == job.id
    assert isinstance(call["messages"], list) and len(call["messages"]) == 1

