from dataclasses import dataclass, field
from typing import List

from app.core.toolkit.tool import Tool


@dataclass
class Action:
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
    next_action_ids: List[str] = field(default_factory=list)
    tools: List[Tool] = field(default_factory=list)

    def copy(self) -> "Action":
        """Create a copy of the action."""
        return Action(
            id=self.id,
            name=self.name,
            description=self.description,
            next_action_ids=list(self.next_action_ids),
            tools=[tool.copy() for tool in self.tools],
        )
