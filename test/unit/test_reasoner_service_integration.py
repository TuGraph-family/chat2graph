from app.core.common.system_env import SystemEnv
from app.core.common.type import ReasonerType
from app.core.memory.enhanced.mem_reasoner import EnhancedReasoner
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.service.reasoner_service import ReasonerService


def test_reasoner_service_wraps_when_enabled():
    """Test that the ReasonerService wraps the reasoner with EnhancedReasoner when
    ENABLE_MEMFUSE is True."""
    SystemEnv.ENABLE_MEMFUSE = True
    svc = ReasonerService()
    svc.init_reasoner(ReasonerType.MONO)
    r = svc.get_reasoner()
    assert isinstance(r, EnhancedReasoner)


def test_reasoner_service_no_wrap_when_disabled():
    """Test that the ReasonerService does not wrap the reasoner with EnhancedReasoner when
    ENABLE_MEMFUSE is False."""
    SystemEnv.ENABLE_MEMFUSE = False
    svc = ReasonerService()
    # ensure we reset constructed reasoner
    svc.init_reasoner(ReasonerType.MONO)
    r = svc.get_reasoner()
    assert not isinstance(r, EnhancedReasoner)
    assert isinstance(r, MonoModelReasoner)

