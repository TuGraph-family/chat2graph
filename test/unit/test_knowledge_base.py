import time
from typing import List
from unittest.mock import AsyncMock, patch
import os

import pytest

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.plugin.dbgpt.dbgpt_knowledge_base import VectorKnowledgeBase, GraphKnowledgeBase
from app.core.service.knowledge_base_service import KnowledgeBaseService
from app.core.dal.init_db import init_db
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.job import SubJob

init_db()
# initialize the dao
DaoFactory.initialize(DbSession())
knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService()


async def test_vector_knowledge_base():
    chunks = VectorKnowledgeBase("test_vector_knowledge_base").retrieve("what is awel talk about")
    assert len(chunks) == 0

    chunk_ids = VectorKnowledgeBase("test_vector_knowledge_base").load_document(
        SystemEnv.APP_ROOT + "/global_knowledge/awel.md"
    )
    chunks = VectorKnowledgeBase("test_vector_knowledge_base").retrieve("what is awel talk about")
    assert len(chunks) != 0

    VectorKnowledgeBase("test_vector_knowledge_base").delete_document(chunk_ids)
    chunks = VectorKnowledgeBase("test_vector_knowledge_base").retrieve("what is awel talk about")
    assert len(chunks) == 0

async def test_graph_knowledge_base():
    chunks = GraphKnowledgeBase("test_graph_knowledge_base").retrieve("what is awel talk about")
    assert len(chunks) == 0

    GraphKnowledgeBase("test_graph_knowledge_base").load_document(
        SystemEnv.APP_ROOT + "/global_knowledge/awel.md"
    )
    chunks = GraphKnowledgeBase("test_graph_knowledge_base").retrieve("what is awel talk about")
    assert len(chunks) != 0

async def test_knowledge_base_service():
    job = SubJob(
        id="test_job_id", session_id="test_session_id", goal="Test goal", context="Test context"
    )
    knowledge = KnowledgeBaseService.instance.get_knowledge(
        query="what is awel talk about", job=job
    )
    assert "[Knowledges From Gloabal Knowledge Base]" in knowledge.get_payload()
    assert "[Knowledges From Local Knowledge Base]" in knowledge.get_payload()
