from abc import ABC
from typing import List

from app.env.consensus.consensus_manager import ConsensusManager
from app.env.insight.insight_data import InsightData
from app.env.insight.insight_manager import TextInsightManager


class EnvManager(ABC):
    """Environment Manager manages the environment of the multi-agent system."""

    def __init__(self):
        self.consensus_manager = ConsensusManager()
        self.text_insight_manager = TextInsightManager()
        self.image_insight_manager = None
        self.table_insight_manager = None

    async def recommend_info(self, data: str) -> str:
        """Recommend information."""
        insights: List[
            InsightData
        ] = await self.text_insight_manager.retrieve_insights()

        return ""
