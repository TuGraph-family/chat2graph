from app.core.toolkit.tool import Tool


class BroswerUseTool(Tool):
    """A tool to use broswer."""

    def __init__(self):
        super().__init__(
            name=self.use_broswer.__name__,
            description=self.use_broswer.__doc__ or "",
            function=self.use_broswer,
        )

    async def use_broswer(self, task_prompt: str) -> str:
        """Given a task prompt, use broswer to search and return the result.

        Args:
            task_prompt (str): The task prompt to search.
        
        Returns:
            str: The result of the search.
        """
