from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import List
from uuid import uuid4


class InsightType(Enum):
    """Insight Type"""

    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"


@dataclass
class Insight:
    """Insight is an element of the environment."""

    tags: List[str]

    id: str = field(default_factory=lambda: str(uuid4()))

    def to_json(self):
        """Convert to JSON."""
        return asdict(self)


@dataclass
class TextInsight(Insight):
    """Text Insight"""

    content: str = ""
    entities: List[str] = field(default_factory=list)
    insight_type: InsightType = InsightType.TEXT


@dataclass
class ImageInsight(Insight):
    """Image Insight"""

    image_url: str = ""
    insight_type: InsightType = InsightType.IMAGE

    # TODO: add more fields


@dataclass
class TableInsight(Insight):
    """Table Insight"""

    insight_type: InsightType = InsightType.TABLE

    # TODO: add more fields
