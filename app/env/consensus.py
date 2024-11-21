from dataclasses import dataclass
from typing import List


@dataclass
class Consensus:
    """Consensus is rarely modified in the environment."""

    id: str
    tags: List[str]
    content: str
