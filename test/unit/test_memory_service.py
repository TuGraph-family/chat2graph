from uuid import uuid4

from app.core.common.system_env import SystemEnv
from app.core.memory.memory import BuiltinMemory
from app.core.model.task import MemoryKey
from app.core.sdk.init_server import init_server
from app.core.service.memory_service import MemoryService
from app.plugin.memfuse.operator_memory import MemFuseOperatorMemory
from app.plugin.memfuse.reasoner_memory import MemFuseReasonerMemory

init_server()


def test_factory_builtin_when_disabled():
    """When MemFuse is disabled, the factory should create BuiltinReasonerMemory."""
    SystemEnv.ENABLE_MEMFUSE = False
    ms = MemoryService()
    mem = ms.get_or_create_reasoner_memory(
        MemoryKey(job_id="job_test_builtin" + str(uuid4()), operator_id="op_a" + str(uuid4()))
    )
    assert isinstance(mem, BuiltinMemory)


def test_reasoner_memory_factory_when_memfuse_enabled():
    """When MemFuse is enabled, the factory should create MemFuseMemory."""
    SystemEnv.ENABLE_MEMFUSE = True

    ms: MemoryService = MemoryService.instance
    mem = ms.get_or_create_reasoner_memory(
        MemoryKey(job_id="job_test_builtin" + str(uuid4()), operator_id="op_a" + str(uuid4()))
    )
    assert isinstance(mem, MemFuseReasonerMemory)


def test_operator_memory_factory_when_memfuse_enabled():
    """When MemFuse is enabled, the factory should create MemFuseMemory."""
    SystemEnv.ENABLE_MEMFUSE = True

    ms: MemoryService = MemoryService.instance
    mem = ms.get_or_create_operator_memory(
        MemoryKey(job_id="job_test_builtin" + str(uuid4()), operator_id="op_a" + str(uuid4()))
    )
    assert isinstance(mem, MemFuseOperatorMemory)
