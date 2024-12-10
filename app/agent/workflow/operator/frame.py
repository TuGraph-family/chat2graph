from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Frame:
    """Frame is used to transfer the metadata between the operators in the workflow."""

    id: str = field(default_factory=lambda: str(uuid4()))
    scratchpad: str = ""
