from dataclasses import dataclass
from typing import List


@dataclass
class Consensus:
    """Consensus dataclass, which is rarely modified"""

    id: str
    tags: List[str]
    content: str
