from app.core.common.system_env import SystemEnv
from app.core.common.type import ModelPlatformType


def test_system_env():
    """Test the system environment."""
    assert type(SystemEnv.PATH), str
    assert SystemEnv.MODEL_PLATFORM_TYPE, ModelPlatformType.LITELLM
    assert not SystemEnv.XXX
