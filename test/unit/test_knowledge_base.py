from unittest.mock import patch
from uuid import uuid4

from dbgpt.core import Chunk

from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.dal.init_db import init_db
from app.core.model.job import SubJob
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.plugin.dbgpt.dbgpt_knowledge_store import VectorKnowledgeStore

init_db()
# initialize the dao
DaoFactory.initialize(DbSession())
knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService()


async def test_vector_knowledge_base():
    """Test vector knowledge base."""
    with patch(
        "dbgpt.rag.retriever.embedding.EmbeddingRetriever.aretrieve_with_scores"
    ) as mock_retrieve:
        mock_retrieve.return_value = [Chunk(), Chunk(), Chunk()]
        chunks = VectorKnowledgeStore("test_vector_knowledge_base").retrieve(
            "what is chat2graph talk about"
        )
        assert len(chunks) != 0


async def test_knowledge_base_service():
    """Test knowledge base service."""
    job = SubJob(
        id="test_job_id" + str(uuid4()),
        session_id="test_session_id " + str(uuid4()),
        goal="Test goal",
        context="Test context",
    )
    knowledge_service: KnowledgeBaseService = KnowledgeBaseService.instance
    knowledge = knowledge_service.get_knowledge(
        query="what is chat2graph talk about", session_id=job.session_id
    )
    assert (
        "[Knowledges From Global Knowledge Base]" in knowledge.get_payload()
        or "No knowledge found" in knowledge.get_payload()
    )
    assert (
        "[Knowledges From Local Knowledge Base]" in knowledge.get_payload()
        or "No knowledge found" in knowledge.get_payload()
    )
