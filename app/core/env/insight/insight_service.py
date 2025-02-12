from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.core.env.insight.insight import Insight, InsightType


class InsightService(ABC):
    """Insight Service"""

    def __init__(self, insights: Optional[List[Insight]] = None):
        self._insights: List[Insight] = insights or []

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


class TextInsightService(InsightService):
    """Text Insight Service"""

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
        return [insight.to_json() for insight in self._insights]


# TODO: multi-modal insights
class ImageInsightService(InsightService):
    """Image Insight Service"""

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
        return [insight.to_json() for insight in self._insights]


# TODO: multi-modal insights for table RAG
class TableInsightService(InsightService):
    """Table Insight Service"""

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
        return [insight.to_json() for insight in self._insights]


class InsightServiceFactory:
    """Insight Server Factory"""

    @staticmethod
    def create_insight_service(insight_type) -> InsightService:
        """Create an insight server."""
        if insight_type == InsightType.TEXT:
            return TextInsightService()
        if insight_type == InsightType.IMAGE:
            return ImageInsightService()
        if insight_type == InsightType.TABLE:
            return TableInsightService()
        raise ValueError("Invalid insight type.")
