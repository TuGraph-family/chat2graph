from typing import List

from app.toolkit.action.action import Action
from app.toolkit.tool.tool import Tool


class Operator:
    """Operator is a sequence of actions and tools that need to be executed."""

    def __init__(self):
        self.actions: List[Action] = None
        self.tools: List[Tool] = None

        self.context_prompt: str = self.set_context_prompt()

    def set_context_prompt(self) -> str:
        """Set the context prompt by combining the actions and the tools."""

    def execute(self):
        """Execute the operator by LLM client."""
