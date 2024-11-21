from abc import ABC
from dataclasses import dataclass
from typing import List

from app.toolkit.tool.tool import Tool


@dataclass
class Action(ABC):
    """Action in the toolkit."""

    id: str
    name: str
    description: str
    next_action_names: List[str] = None
    tools: List[Tool] = None
