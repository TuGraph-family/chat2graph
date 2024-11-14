from abc import ABC
from dataclasses import dataclass
from typing import List

from app.toolkit.tool.tool import Tool


@dataclass
class Action(ABC):
    """The action in the toolkit."""

    id: str
    name: str
    next_action_names: List[str]
    description: str
    tools: List[Tool]
