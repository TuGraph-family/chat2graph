import pytest

from app.core.common.system_env import SystemEnv
from app.core.memory.enhanced.hook import MemFuseOperatorHook
from app.core.model.job import Job
from app.core.model.task import Task
from app.core.workflow.operator_config import OperatorConfig
from app.core.service.memory_service import MemoryService


class _StubMem:
    def __init__(self):
        self.calls = []

    def write_turn(self, sys_prompt, messages, job_id, operator_id):  # noqa: ARG002
        self.calls.append({
            "sys_prompt": sys_prompt,
            "messages": messages,
            "job_id": job_id,
            "operator_id": operator_id,
        })


@pytest.mark.asyncio
async def test_operator_post_execute_writes_turn(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = True

    job = Job(goal="Write report", context="on Q3 metrics")
    task = Task(job=job, operator_config=OperatorConfig(instruction="Summarize data", actions=[]))

    stub = _StubMem()
    monkeypatch.setattr(
        MemoryService,
        "get_or_create_operator_memory",
        lambda self, job_id, operator_id: stub,  # noqa: ARG002
    )

    hook = MemFuseOperatorHook()
    await hook.post_execute(task, result="All KPIs up")

    assert len(stub.calls) == 1
    call = stub.calls[0]
    # sys prompt contains operator instruction and job goal/context
    assert "[operator_instruction]" in call["sys_prompt"]
    assert "Summarize data" in call["sys_prompt"]
    assert "goal: Write report" in call["sys_prompt"]
    assert "context: on Q3 metrics" in call["sys_prompt"]
    # messages contains one assistant message with result payload
    assert len(call["messages"]) == 1
    assert call["messages"][0].get_payload() == "All KPIs up"


@pytest.mark.asyncio
async def test_operator_post_execute_disabled_noop(monkeypatch):
    SystemEnv.ENABLE_MEMFUSE = False

    job = Job(goal="X", context="Y")
    task = Task(job=job, operator_config=OperatorConfig(instruction="Z", actions=[]))

    stub = _StubMem()
    monkeypatch.setattr(
        MemoryService,
        "get_or_create_operator_memory",
        lambda self, job_id, operator_id: stub,  # noqa: ARG002
    )

    hook = MemFuseOperatorHook()
    await hook.post_execute(task, result="ignored")

    assert stub.calls == []

