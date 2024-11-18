from pydantic import BaseModel

from app.toolkit.tool.tool import Tool


class QuerySchema(BaseModel):
    """The query schema."""

    text: str


class Query(Tool):
    """The query tool in the toolkit."""

    def __init__(self):
        super().__init__(self.query, args_schema=QuerySchema)

    def query(self, text: str) -> str:
        """Query the text."""
        return text
