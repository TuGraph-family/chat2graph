from unittest.mock import patch

from app.plugin.dbgpt.dbgpt_knowledge_store import VectorKnowledgeStore, GraphKnowledgeStore
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.dal.init_db import init_db
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.job import SubJob
from dbgpt.core import Chunk

init_db()
# initialize the dao
DaoFactory.initialize(DbSession())
knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService()


async def test_vector_knowledge_base():
    with patch(
        "dbgpt.rag.retriever.embedding.EmbeddingRetriever.aretrieve_with_scores"
    ) as mock_retrieve:
        mock_retrieve.return_value = [Chunk(), Chunk(), Chunk()]
        chunks = VectorKnowledgeStore("test_vector_knowledge_base").retrieve(
            "what is chat2graph talk about"
        )
        assert len(chunks) != 0

        # chunk_ids = VectorKnowledgeStore("test_vector_knowledge_base").load_document("./chat2graph.md")
        # chunks = VectorKnowledgeStore("test_vector_knowledge_base").retrieve("what is chat2graph talk about")
        # assert len(chunks) != 0

        # VectorKnowledgeStore("test_vector_knowledge_base").delete_document(chunk_ids)
        # chunks = VectorKnowledgeStore("test_vector_knowledge_base").retrieve("what is chat2graph talk about")
        # assert len(chunks) == 0


async def test_graph_knowledge_base():
    with patch(
        "dbgpt_ext.storage.knowledge_graph.community_summary.CommunitySummaryKnowledgeGraph.asimilar_search_with_scores"
    ) as mock_retrieve:
        mock_retrieve.return_value = [Chunk(), Chunk(), Chunk()]
        chunks = GraphKnowledgeStore("test_graph_knowledge_base").retrieve(
            "what is chat2graph talk about"
        )
        assert len(chunks) != 0


async def test_knowledge_base_service():
    job = SubJob(
        id="test_job_id", session_id="test_session_id", goal="Test goal", context="Test context"
    )
    knowledge = KnowledgeBaseService.instance.get_knowledge(
        query="what is chat2graph talk about", job=job
    )
    assert "[Knowledges From Global Knowledge Base]" in knowledge.get_payload()
    assert "[Knowledges From Local Knowledge Base]" in knowledge.get_payload()
