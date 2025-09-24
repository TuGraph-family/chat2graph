from app.core.common.system_env import SystemEnv
from app.core.memory.reasoner_memory import BuiltinReasonerMemory
from app.core.service.memory_service import MemoryService


def test_factory_builtin_when_disabled():
    SystemEnv.ENABLE_MEMFUSE = False
    ms = MemoryService()
    mem = ms.get_or_create_reasoner_memory("job_test_builtin", "op_a")
    assert isinstance(mem, BuiltinReasonerMemory)


def test_factory_memfuse_when_enabled():
    SystemEnv.ENABLE_MEMFUSE = True
    from app.core.memory.memfuse_memory import MemFuseMemory

    ms = MemoryService()
    mem = ms.get_or_create_reasoner_memory("job_test_memfuse", "op_b")
    assert isinstance(mem, MemFuseMemory)


def test_system_env_typing_setattr_roundtrip():
    # bool casting
    SystemEnv.ENABLE_MEMFUSE = "true"
    assert SystemEnv.ENABLE_MEMFUSE is True
    SystemEnv.ENABLE_MEMFUSE = "0"
    assert SystemEnv.ENABLE_MEMFUSE is False

    # float casting
    SystemEnv.MEMFUSE_TIMEOUT = "45.5"
    assert isinstance(SystemEnv.MEMFUSE_TIMEOUT, float)
    assert SystemEnv.MEMFUSE_TIMEOUT == 45.5

    # int casting
    SystemEnv.MEMFUSE_RETRY_COUNT = "7"
    assert isinstance(SystemEnv.MEMFUSE_RETRY_COUNT, int)
    assert SystemEnv.MEMFUSE_RETRY_COUNT == 7

    # str roundtrip
    SystemEnv.MEMFUSE_BASE_URL = "http://example.local:1234"
    assert SystemEnv.MEMFUSE_BASE_URL == "http://example.local:1234"
