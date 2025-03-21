import os
from typing import Any, Dict, List, Optional

from app.core.knowledge.knowledge_base import KnowledgeBase

from dbgpt.configs.model_config import MODEL_PATH, PILOT_PATH, ROOT_PATH
from dbgpt.rag.index.base import IndexStoreBase, IndexStoreConfig
from dbgpt.storage.vector_store.base import VectorStoreBase, VectorStoreConfig
from dbgpt.rag.embedding import DefaultEmbeddingFactory
from dbgpt.storage.vector_store.chroma_store import ChromaStore, ChromaVectorConfig
from dbgpt.storage.knowledge_graph.base import KnowledgeGraphBase, KnowledgeGraphConfig
from dbgpt.storage.knowledge_graph.knowledge_graph import (
    BuiltinKnowledgeGraph,
    BuiltinKnowledgeGraphConfig,
)
from dbgpt.storage.knowledge_graph.community_summary import (
    CommunitySummaryKnowledgeGraph,
    CommunitySummaryKnowledgeGraphConfig,
)
from dbgpt.storage.full_text.base import FullTextStoreBase
from dbgpt.rag.retriever.embedding import EmbeddingRetriever
from dbgpt.rag.knowledge import KnowledgeFactory
from dbgpt.rag import ChunkParameters
from dbgpt.rag.assembler import EmbeddingAssembler
from dbgpt.rag.retriever import RetrieverStrategy
from dbgpt.model.proxy.llms.tongyi import TongyiLLMClient
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient
from app.core.common.system_env import SystemEnv
from app.core.common.async_func import run_async_function
from app.core.common.type import PlatformType
from app.core.reasoner.model_service_factory import ModelServiceFactory

model_service = ModelServiceFactory.create(platform_type=PlatformType.DBGPT)


class VectorKnowledgeBase(KnowledgeBase):
    """Knowledge base for storing vectors."""

    def __init__(self, name):
        config = ChromaVectorConfig(
            persist_path=SystemEnv.APP_ROOT + "/knowledge_base",
            name=name,
            embedding_fn=DefaultEmbeddingFactory(
                default_model_name=os.path.join(
                    SystemEnv.APP_ROOT + "/models", SystemEnv.EMBEDDING_MODEL
                ),
            ).create(),
        )
        self._vector_base = ChromaStore(config)
        self._retriever = EmbeddingRetriever(
            top_k=3,
            index_store=self._vector_base,
        )
        self._chunk_id_dict = {}

    def load_document(self, file_path, config=None) -> str:
        knowledge = KnowledgeFactory.from_file_path(file_path)
        if config:
            chunk_parameters = ChunkParameters(
                chunk_strategy="CHUNK_BY_SIZE", chunk_size=int(config["chunk_size"])
            )
        else:
            chunk_parameters = ChunkParameters(chunk_strategy="CHUNK_BY_SIZE")
        assembler = EmbeddingAssembler.load_from_knowledge(
            knowledge=knowledge, chunk_parameters=chunk_parameters, index_store=self._vector_base
        )
        chunk_ids = run_async_function(assembler.apersist)
        self._chunk_id_dict[file_path] = ",".join(chunk_ids)
        return ",".join(chunk_ids)

    def delete_document(self, chunk_ids):
        self._vector_base.delete_by_ids(chunk_ids)

    def update_document(self, file_path, chunk_ids):
        self.delete_document(chunk_ids)
        return run_async_function(self.load_document, file_path=file_path)

    def retrieve(self, query):
        chunks = run_async_function(
            self._retriever.aretrieve_with_scores, query=query, score_threshold=0.3
        )
        return chunks

    def clear(self):
        file_path_list = list(self._chunk_id_dict.keys)
        for file_path in file_path_list:
            self.delete_document(self._chunk_id_dict[file_path])

    def delete(self):
        self._vector_base._clean_persist_folder()

