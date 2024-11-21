from abc import ABC
from dataclasses import dataclass
from typing import List

from app.toolkit.tool.tool import Tool


@dataclass
class Action(ABC):
    """The action in the toolkit.

    Attributes:
        id (str): The unique identifier of the action.
        name (str): The name of the action.
        description (str): The description of the action.
        next_action_names (List[str]): The names of the next actions in the toolkit.
        tools (List[Tool]): The tools can be used in the action.
    """

    id: str
    name: str
    description: str
    next_action_names: List[str] = None
    tools: List[Tool] = None
