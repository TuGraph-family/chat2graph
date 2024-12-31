from dataclasses import dataclass, field
from typing import List
from uuid import uuid4

from app.toolkit.action.action import Action


@dataclass
class OperatorConfig:
    """Operator configuration."""

    instruction: str
    actions: List[Action]
    id: str = field(default_factory=lambda: str(uuid4()))
    output_schema: str = ""
    threshold: float = 0.5
    hops: int = 0
