import time
from typing import List
from unittest.mock import AsyncMock, patch
import os

import pytest

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.plugin.dbgpt.dbgpt_knowledge_base import VectorKnowledgeBase
from app.core.service.knowledge_base_service import KnowledgeBaseService

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GLOBAL_KNOWLEDGE_PATH = ROOT_PATH + "/app/core/knowledge/global_knowledge"

async def test_vector_knowledge_base():
    chunks = await VectorKnowledgeBase("test_vector_knowledge_base").retrieve("what is awel talk about")
    print(chunks)
    print("---------------------")

    chunk_ids = await VectorKnowledgeBase("test_vector_knowledge_base").load_document(GLOBAL_KNOWLEDGE_PATH)
    chunks = await VectorKnowledgeBase("test_vector_knowledge_base").retrieve("what is awel talk about")
    print(chunks)
    print("---------------------")

    VectorKnowledgeBase("test_vector_knowledge_base").delete_document(chunk_ids)
    chunks = await VectorKnowledgeBase("test_vector_knowledge_base").retrieve("what is awel talk about")
    print(chunks)

async def test_knowledge_base_service():
    print(GLOBAL_KNOWLEDGE_PATH)
    knowledge_base_service: KnowledgeBaseService = KnowledgeBaseService()
    await KnowledgeBaseService.instance.load_global_knowledge(GLOBAL_KNOWLEDGE_PATH)
    knowledge = await KnowledgeBaseService.instance.get_knowledge(query="what is awel talk about",session_id="test_knowledge_base_service")
    print(knowledge.get_payload())
