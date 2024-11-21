from pydantic import BaseModel

from app.toolkit.tool.tool import Tool


class QuerySchema(BaseModel):
    """Query schema."""

    text: str


class Query(Tool):
    """Query tool in the toolkit."""

    def __init__(self):
        super().__init__(self.query, args_schema=QuerySchema)

    def query(self, text: str) -> str:
        """Query the text."""
        return text
