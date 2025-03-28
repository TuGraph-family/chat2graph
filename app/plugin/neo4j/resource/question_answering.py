from typing import List, Optional, Tuple
from uuid import uuid4

from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.toolkit.tool import Tool


class KnowledgeBaseRetriever(Tool):
    """Tool for retrieving document content from knowledge base."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.knowledge_base_search.__name__,
            description=self.knowledge_base_search.__doc__ or "",
            function=self.knowledge_base_search,
        )

    async def knowledge_base_search(
        self, question: str, session_id: str, knowledge_service: KnowledgeBaseService
    ) -> str:
        """Retrive a list of related contents and a list of their reference name from knowledge
        base given the question and current session_id.

        Args:
            question (str): The question asked by user.
            session_id (str): Current session_id.

        Returns:
            str: The related content and reference name in knowledge base.
        """
        knowledge = knowledge_service.get_knowledge(question, session_id)
        if len(knowledge.global_chunks) == 0 and len(knowledge.local_chunks) == 0:
            return (
                "Knowledge base does not have the related knowledge you need, "
                "please consider generate the answer by yourself."
            )
        return knowledge.get_payload()


class InternetRetriever(Tool):
    """Tool for retrieving webpage contents from Internet."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.internet_search.__name__,
            description=self.internet_search.__doc__ or "",
            function=self.internet_search,
        )

    async def internet_search(self, question: str) -> Tuple[List[str], List[str]]:
        """Retrive a list of related webpage contents and a list of their URL references from
        Internet given the question.

        Args:
            question (str): The question asked by user.

        Returns:
            Tuple[List[str], List[str]]: The list of related webpage contents and the list of URL
            references.
        """
        # TODO: implement a web search tool
        return [], []
