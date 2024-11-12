from abc import ABC, abstractmethod
from typing import Any, List

from app.env.insight.insight_data import InsightData, InsightType


class BaseInsightManager(ABC):
    """Base Insight, an env element of the multi-agent system."""

    def __init__(self, insight_data: List[InsightData] = None):
        self.insights: List[InsightData] = insight_data or []

    @abstractmethod
    async def generate_insights(self, data: Any):
        """Generate insights from the data."""

    @abstractmethod
    async def retrieve_insights(self):
        """Retrieve insights."""

    @abstractmethod
    async def merge_insights(self):
        """Merge insights."""

    @abstractmethod
    async def refine_insights(self):
        """Refine insights."""

    @abstractmethod
    async def insights_to_json(self):
        """Convert insights to json."""


class TextInsightManager(BaseInsightManager):
    """Text Insight"""

    async def generate_insights(self, data: Any):
        """Generate insights from the text."""

    async def retrieve_insights(self):
        """Retrieve insights."""

    async def merge_insights(self):
        """Merge insights."""

    async def refine_insights(self):
        """Refine insights."""

    async def insights_to_json(self):
        """Convert insights to json."""
        return [insight.to_json() for insight in self.insights]


# TODO: multi-modal insights
class ImageInsightManager(BaseInsightManager):
    """Image Insight"""

    async def generate_insights(self, data: Any):
        """Generate insights from the image."""

    async def retrieve_insights(self):
        """Retrieve insights."""

    async def merge_insights(self):
        """Merge insights."""

    async def refine_insights(self):
        """Refine insights."""

    async def insights_to_json(self):
        """Convert insights to json."""
        return [insight.to_json() for insight in self.insights]


# TODO: multi-modal insights for table RAG
class TableInsightManager(BaseInsightManager):
    """Table Insight"""

    async def generate_insights(self, data: Any):
        """Generate insights from the table."""

    async def retrieve_insights(self):
        """Retrieve insights."""

    async def merge_insights(self):
        """Merge insights."""

    async def refine_insights(self):
        """Refine insights."""

    async def insights_to_json(self):
        """Convert insights to json."""
        return [insight.to_json() for insight in self.insights]


class InsightManagerFactory:
    """Insight Factory"""

    @staticmethod
    def create_insight(insight_data: InsightData) -> BaseInsightManager:
        """Create an insight."""
        if insight_data.insight_type == InsightType.TEXT:
            return TextInsightManager(insight_data)
        if insight_data.insight_type == InsightType.IMAGE:
            return ImageInsightManager(insight_data)
        if insight_data.insight_type == InsightType.TABLE:
            return TableInsightManager(insight_data)
        raise ValueError("Invalid insight type.")
