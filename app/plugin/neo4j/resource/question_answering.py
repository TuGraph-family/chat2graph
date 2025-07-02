from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.toolkit.tool import Tool


class KnowledgeBaseRetriever(Tool):
    """Tool for retrieving document content from knowledge base."""

    def __init__(self):
        super().__init__(
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
