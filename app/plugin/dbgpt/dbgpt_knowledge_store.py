import os
from typing import List, Optional

from dbgpt.rag.embedding import DefaultEmbeddingFactory  # type: ignore
from dbgpt.rag.retriever import RetrieverStrategy  # type: ignore
from dbgpt.rag.retriever.embedding import EmbeddingRetriever  # type: ignore
from dbgpt_ext.rag.assembler import EmbeddingAssembler  # type: ignore
from dbgpt_ext.rag.chunk_manager import ChunkParameters  # type: ignore
from dbgpt_ext.rag.knowledge.factory import KnowledgeFactory  # type: ignore
from dbgpt_ext.storage.graph_store.tugraph_store import TuGraphStoreConfig  # type: ignore
from dbgpt_ext.storage.knowledge_graph.community_summary import (  # type: ignore
    CommunitySummaryKnowledgeGraph,
)
from dbgpt_ext.storage.vector_store.chroma_store import (  # type: ignore
    ChromaStore,
    ChromaVectorConfig,
)

from app.core.common.async_func import run_async_function
from app.core.common.system_env import SystemEnv
from app.core.knowledge.knowledge_config import KnowledgeConfig
from app.core.knowledge.knowledge_store import KnowledgeStore
from app.core.model.knowledge import KnowledgeChunk
from app.plugin.dbgpt.dbgpt_llm_client import DbgptLlmClient


class VectorKnowledgeStore(KnowledgeStore):
    """Knowledge base for storing vectors."""

    def __init__(self, name: str):
        self._persist_path = f"{SystemEnv.APP_ROOT}{SystemEnv.KNOWLEDGE_STORE_PATH}/{name}"
        config = ChromaVectorConfig(persist_path=self._persist_path)
        self._vector_store = ChromaStore(
            config,
            name=name,
            embedding_fn=DefaultEmbeddingFactory.remote(
                api_url=SystemEnv.EMBEDDING_MODEL_ENDPOINT,
                api_key=SystemEnv.EMBEDDING_MODEL_APIKEY,
                model_name=SystemEnv.EMBEDDING_MODEL_NAME,
            ),
        )
        # TODO add top_k to env config
        self._retriever = EmbeddingRetriever(
            top_k=3,
            index_store=self._vector_store,
        )

    def load_document(self, file_path: str, config: Optional[KnowledgeConfig]) -> str:
        knowledge = KnowledgeFactory.from_file_path(file_path)
        if config:
            chunk_parameters = ChunkParameters(
                chunk_strategy="CHUNK_BY_SIZE", chunk_size=config.chunk_size
            )
        else:
            chunk_parameters = ChunkParameters(chunk_strategy="CHUNK_BY_SIZE")
        assembler = EmbeddingAssembler.load_from_knowledge(
            knowledge=knowledge, chunk_parameters=chunk_parameters, index_store=self._vector_store
        )
        chunk_ids = run_async_function(assembler.apersist)
        return ",".join(chunk_ids)

    def delete_document(self, chunk_ids: str) -> None:
        self._vector_store.delete_by_ids(chunk_ids)

    def update_document(self, file_path: str, chunk_ids: str) -> str:
        self.delete_document(chunk_ids)
        return run_async_function(self.load_document, file_path=file_path)

    def retrieve(self, query: str) -> List[KnowledgeChunk]:
        chunks = run_async_function(
            self._retriever.aretrieve_with_scores, query=query, score_threshold=0.3
        )
        knowledge_chunks = [
            KnowledgeChunk(chunk_name=chunk.chunk_name, content=chunk.content) for chunk in chunks
        ]
        return knowledge_chunks

    def drop(self) -> None:
        self._vector_store._clean_persist_folder()
        os.rmdir(self._persist_path)


class GraphKnowledgeStore(KnowledgeStore):
    """Knowledge base for storing graphs."""

    def __init__(self, name: str):
        config = TuGraphStoreConfig(
            username=SystemEnv.GRAPH_KNOWLEDGE_STORE_USERNAME,
            password=SystemEnv.GRAPH_KNOWLEDGE_STORE_PASSWORD,
            host=SystemEnv.GRAPH_KNOWLEDGE_STORE_HOST,
            port=SystemEnv.GRAPH_KNOWLEDGE_STORE_PORT,
        )
        vector_store_config = ChromaVectorConfig(
            persist_path=SystemEnv.APP_ROOT + SystemEnv.KNOWLEDGE_STORE_PATH
        )
        self._graph_store = CommunitySummaryKnowledgeGraph(
            config=config,
            name=SystemEnv.TUGRAPH_NAME_PREFIX + name.replace("-", ""),
            embedding_fn=DefaultEmbeddingFactory.remote(
                api_url=SystemEnv.EMBEDDING_MODEL_ENDPOINT,
                api_key=SystemEnv.EMBEDDING_MODEL_APIKEY,
                model_name=SystemEnv.EMBEDDING_MODEL_NAME,
            ),
            llm_client=DbgptLlmClient()._llm_client,
            kg_document_graph_enabled=True,
            kg_triplet_graph_enabled=True,
            vector_store_config=vector_store_config,
        )

    def load_document(self, file_path: str, config: Optional[KnowledgeConfig]) -> str:
        knowledge = KnowledgeFactory.from_file_path(file_path)
        if config:
            chunk_parameters = ChunkParameters(
                chunk_strategy="CHUNK_BY_SIZE", chunk_size=config.chunk_size
            )
        else:
            chunk_parameters = ChunkParameters(chunk_strategy="CHUNK_BY_SIZE")
        assembler = EmbeddingAssembler.load_from_knowledge(
            knowledge=knowledge,
            chunk_parameters=chunk_parameters,
            index_store=self._graph_store,
            retrieve_strategy=RetrieverStrategy.GRAPH,
        )
        chunk_ids = run_async_function(assembler.apersist)
        return ",".join(chunk_ids)

    def delete_document(self, chunk_ids: str) -> None:
        self._graph_store.delete_by_ids(chunk_ids)

    def update_document(self, file_path: str, chunk_ids: str) -> str:
        self.delete_document(chunk_ids)
        return run_async_function(self.load_document, file_path=file_path)

    def retrieve(self, query: str) -> List[KnowledgeChunk]:
        chunks = run_async_function(
            self._graph_store.asimilar_search_with_scores, text=query, topk=3, score_threshold=0.3
        )
        knowledge_chunks = [
            KnowledgeChunk(chunk_name=chunk.chunk_name, content=chunk.content) for chunk in chunks
        ]
        return knowledge_chunks

    def drop(self) -> None:
        self._graph_store.delete_vector_name("")
