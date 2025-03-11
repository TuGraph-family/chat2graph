from typing import Optional
from uuid import uuid4

from app.core.common.system_env import SystemEnv
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.core.toolkit.tool import Tool


# example tool
class Query(Tool):
    """The query tool in the toolkit."""

    def __init__(self, id: Optional[str] = None):
        name = self.query.__name__
        description = self.query.__doc__ or ""
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
        model_service = ModelServiceFactory.create(platform_type=SystemEnv.MODEL_PLATFORM_TYPE)
        sys_prompt = """Suppose you are the database or the document terminal.
I will ask you for help. If you don't know the answer, you can make up a reasonable one."""
        message = ModelMessage(payload=text, job_id="query_id", step=1)
        response: ModelMessage = await model_service.generate(
            sys_prompt=sys_prompt, messages=[message]
        )

        return response.get_payload()
