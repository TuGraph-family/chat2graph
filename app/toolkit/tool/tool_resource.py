from typing import Optional

from pydantic import BaseModel

from app.toolkit.tool.tool import Tool


class QuerySchema(BaseModel):
    """Query schema."""

    text: str


class Query(Tool):
    """The query tool in the toolkit."""

    def __init__(self, tool_id: Optional[str] = None):
        super().__init__(tool_id=tool_id, function=self.query, args_schema=QuerySchema)

    def query(self, text: str) -> str:
        """Query the text."""
        return text
