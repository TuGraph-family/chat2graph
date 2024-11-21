from dataclasses import dataclass
from typing import List

from app.env.insight.insight_service import TextInsightService


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
        self._text_insight_server = TextInsightService()
        self._image_insight_server = None
        self._table_insight_server = None

    async def recommend_info(self, data: str) -> str:
        """Recommend information."""
