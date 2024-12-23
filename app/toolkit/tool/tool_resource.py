import time
from typing import Optional
from uuid import uuid4

from app.agent.reasoner.model_service_factory import ModelServiceFactory
from app.commom.type import PlatformType
from app.memory.message import ModelMessage
from app.toolkit.tool.tool import Tool


# example tool
class Query(Tool):
    """The query tool in the toolkit."""

    def __init__(self, id: Optional[str] = None):
        name = self.query.__name__
        description = self.query.__doc__
        super().__init__(
            name=name,
            description=description,
            function=self.query,
            id=id or str(uuid4()),
        )

    async def query(self, text: str) -> str:
        """Query the database/document by the text.

        Args:
            text: The text to query.

        Returns:
            The result of the query from the database/document.
        """
        # TODO: implement the query function
        model_service = ModelServiceFactory.create(platform_type=PlatformType.DBGPT)
        sys_prompt = """Suppose you are the database or the document terminal.
I will ask you for help. If you don't know the answer, you can make up a reasonable one."""
        message = ModelMessage(
            content=text,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        response: ModelMessage = await model_service.generate(
            sys_prompt=sys_prompt, messages=[message]
        )

        return response.get_payload()
