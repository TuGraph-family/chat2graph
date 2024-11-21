from dataclasses import asdict, dataclass
from enum import Enum
from typing import List


class InsightType(Enum):
    """Insight Type"""

    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"


@dataclass
class Insight:
    """Insight Data"""

    id: str
    insight_type: InsightType
    tags: List[str]

    def to_json(self):
        """Convert to JSON."""
        return asdict(self)


@dataclass
class TextInsight(Insight):
    """Insight Data"""

    insight_type: InsightType = InsightType.TEXT
    entities: List[str]
    content: str


@dataclass
class ImageInsight(Insight):
    """Insight Data"""

    insight_type: InsightType = InsightType.IMAGE
    image_url: str

    # TODO: add more fields


@dataclass
class TableInsight(Insight):
    """Insight Data"""

    insight_type: InsightType = InsightType.TABLE

    # TODO: add more fields
