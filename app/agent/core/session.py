from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Session:
    """Chat session."""

    id: str = field(default_factory=lambda: str(uuid4()))
