from dataclasses import dataclass
from typing import List

from app.toolkit.tool.tool import Tool


@dataclass
class Action:
    """The action in the toolkit."""

    id: str
    name: str
    description: str
    tools: List[Tool]
