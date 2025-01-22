from dataclasses import dataclass, field
from uuid import uuid4

from app.common.decorator import session_wrapper


@session_wrapper
@dataclass
class Session:
    """Session class"""

    id: str = field(default_factory=lambda: str(uuid4()))
