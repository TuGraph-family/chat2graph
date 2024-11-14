from app.toolkit.tool.tool import Tool


class Query(Tool):
    """The query tool in the toolkit."""

    def __init__(self):
        super().__init__(self.query)

    def query(self, text: str) -> str:
        """Query the text."""
        return text
