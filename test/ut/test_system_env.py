from app.core.common.system_env import SystemEnv
from app.core.common.type import PlatformType


def test_system_env():
    """Test the system environment."""
    assert type(SystemEnv.PATH), str
    assert SystemEnv.PLATFORM_TYPE, PlatformType.DBGPT
    assert not SystemEnv.XXX
