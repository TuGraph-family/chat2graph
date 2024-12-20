from dataclasses import asdict, dataclass
from typing import List


@dataclass
class Insight:
    """Insight is an element of the environment."""

    id: str
    tags: List[str]
    entities: List[str]
    content: str

    def to_json(self):
        """Convert to JSON."""
        return asdict(self)


@dataclass
class Consensus:
    """Consensus is rarely modified in the environment."""

    id: str
    tags: List[str]
    content: str


class Env:
    """Environment Manager manages the environment of the multi-agent system."""

    def __init__(self):
        self._consensuses: List[Consensus] = []
        self._insights: List[Insight] = []

    async def recommend_info(self, data: str) -> str:
        """Recommend information."""
        return ""

    async def generate_insights(self):
        """Generate insights from the data."""

    async def retrieve_insights(self):
        """Retrieve insights."""

    async def merge_insights(self):
        """Merge insights."""

    async def refine_insights(self):
        """Refine insights."""

    async def insights_to_json(self):
        """Convert insights to json."""
