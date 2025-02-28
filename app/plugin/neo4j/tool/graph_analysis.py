from typing import Optional
from uuid import uuid4

from app.core.toolkit.tool import Tool


class AlgorithmsGetter(Tool):
    """Tool to get all algorithms from the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.get_algorithms.__name__,
            description=self.get_algorithms.__doc__ or "",
            function=self.get_algorithms,
        )

    async def get_algorithms(self) -> str:
        """Retrieve all algorithm plugins of a specified type and version supported by the graph
        database.
        """

        raise NotImplementedError("This function is not implemented yet.")


class AlgorithmsExecutor(Tool):
    """Tool to execute algorithms on the graph database."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.execute_algorithms.__name__,
            description=self.execute_algorithms.__doc__ or "",
            function=self.execute_algorithms,
        )

    async def execute_algorithms(self, algorithms_name: str) -> str:
        """Execute the specified algorithm on the graph database.

        This function calls the specified algorithm plugin on the graph database and returns the
        result.

        Args:
            algorithms_name (str): The name of the algorithm to execute. Pay attention to the format
            of the algorithm name.

        Returns:
            str: The result of the algorithm execution.
        """
        raise NotImplementedError("This function is not implemented yet.")
