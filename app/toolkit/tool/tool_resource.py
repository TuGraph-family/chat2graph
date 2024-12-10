from typing import Optional

from app.toolkit.tool.tool import Tool


# example tool
class Query(Tool):
    """The query tool in the toolkit."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(id=id, function=self.query)

    def query(self, text: str) -> str:
        """Query the text.

        Args:
            text: The text to query.

        Returns:
            The result of the query.
        """
        # TODO: implement the query function
        return text
