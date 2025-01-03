from app.commom.system_env import SystemEnv
from app.commom.type import PlatformType


def test_system_env():
    assert type(SystemEnv.PATH), str
    assert SystemEnv.PLATFORM_TYPE, PlatformType.DBGPT
    assert not SystemEnv.XXX
