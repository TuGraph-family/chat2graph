from abc import ABC, abstractmethod
from typing import Any, List

from app.env.insight.insight import Insight, InsightType


class InsightServer(ABC):
    """Base Insight, an env element of the multi-agent system."""

    def __init__(self, insights: List[Insight] = None):
        self.insights: List[Insight] = insights or []

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


class TextInsightServer(InsightServer):
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
class ImageInsightServer(InsightServer):
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
class TableInsightServer(InsightServer):
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


class InsightServerFactory:
    """Insight Factory"""

    @staticmethod
    def create_insight_server(insight_type) -> InsightServer:
        """Create an insight server."""
        if insight_type == InsightType.TEXT:
            return TextInsightServer()
        if insight_type == InsightType.IMAGE:
            return ImageInsightServer()
        if insight_type == InsightType.TABLE:
            return TableInsightServer()
        raise ValueError("Invalid insight type.")
