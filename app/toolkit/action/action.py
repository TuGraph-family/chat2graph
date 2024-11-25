from abc import ABC
from dataclasses import dataclass
from typing import List, Optional

from app.toolkit.tool.tool import Tool


@dataclass
class Action(ABC):
    """The action in the toolkit.

    Attributes:
        id (str): The unique identifier of the action.
        name (str): The name of the action.
        description (str): The description of the action.
        next_action_ids (List[str]): The ids of the next actions in the toolkit.
        tools (List[Tool]): The tools can be used in the action.
    """

    id: str
    name: str
    description: str
    next_action_ids: Optional[List[str]] = None
    tools: Optional[List[Tool]] = None
