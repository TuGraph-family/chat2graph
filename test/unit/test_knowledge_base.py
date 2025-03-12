import time
from typing import List
from unittest.mock import AsyncMock, patch

import pytest

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.reasoner.model_service_factory import ModelServiceFactory
from app.plugin.dbgpt.dbgpt_knowledge_base import VectorKnowledgeBase, GraphKnowledgeBase

async def test_vector_knowledge_base():
    knowledge_base = VectorKnowledgeBase("test_vector_knowledge_base")
    # await knowledge_base.load_document("./awel.md")
    # chunks = await knowledge_base.retrieve("what is awel talk about")
    # print(chunks)
    print("---------------------")
    knowledge_base.delete_document("./awel.md")
    chunks = await knowledge_base.retrieve("what is awel talk about")
    print(chunks)

# async def test_graph_knowledge_base():
#     knowledge_base = GraphKnowledgeBase("test_graph_knowledge_base")
#     # await knowledge_base.load_document("./awel.md")
#     chunks = await knowledge_base.retrieve("AWEL是什么?")
#     print(chunks)
#     # print("---------------------")
#     # knowledge_base.delete_document("./awel.md")
#     # chunks = await knowledge_base.retrieve("AWEL是什么?")
#     # print(chunks)
