from app.core.toolkit.tool import Tool


# example tool
class ExampleQuery(Tool):
    """The query tool in the toolkit."""

    def __init__(self):
        super().__init__(
            name="query_tool",
            description="A test query tool",
            function=self.query,
        )

    async def query(self, text: str) -> str:
        """Query the database/document by the text.

        Args:
            text: The text to query.

        Returns:
            The result of the query from the database/document.
        """
        return "This is a mocked query result"

    def copy(self) -> "ExampleQuery":
        """Create a copy of the ExampleQuery tool."""
        return ExampleQuery()
