from typing import List, Optional, Tuple
from uuid import uuid4

from app.core.toolkit.tool import Tool
from app.core.service.knowledge_base_service import KnowledgeBaseService


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
        self, question: str, session_id: str
    ) -> Tuple[List[str], List[str]]:
        """Retrive a list of related contents and a list of their reference name from knowledge
        base given the question and the session id of current job.

        Args:
            question (str): The question asked by user.
            session_id (str): The session id of current job.

        Returns:
            (List[str], List[str]): The list of related contents and the list of reference name.
        """

        knowledge = KnowledgeBaseService.instance.get_knowledge(question, session_id)
        global_chunks = knowledge.global_chunks
        local_chunks = knowledge.local_chunks
        contents = []
        refs = []
        for chunk in global_chunks:
            contents.append(chunk.content)
            refs.append(chunk.chunk_name)
        for chunk in local_chunks:
            contents.append(chunk.content)
            refs.append(chunk.chunk_name)

        return contents, refs


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

        # TODO: implement a web search sdk
        return [], []


class ReferenceGenerator(Tool):
    """Tool for generating rich text references."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.reference_listing.__name__,
            description=self.reference_listing.__doc__ or "",
            function=self.reference_listing,
        )

    async def reference_listing(
        self, knowledge_base_references: List[str], internet_references: List[str]
    ) -> List[str]:
        """Return a rich text references list for better presentation given the list of references.

        Args:
            knowledge_base_references (List[str]): references from knowledge base.
            internet_references (List[str]): references from internet.

        Returns:
            str: The rich text to demonstrate all references.
        """

        reference_list: List[str] = []
        for knowledge_base_ref in knowledge_base_references:
            reference_list.append(f"[{knowledge_base_ref}]()")
        for inernet_ref in internet_references:
            reference_list.append(f"[网页链接]({inernet_ref})")

        return reference_list
