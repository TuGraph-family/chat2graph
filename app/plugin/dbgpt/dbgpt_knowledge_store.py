from typing import List, Optional

from app.core.knowledge.knowledge_store import KnowledgeStore

from dbgpt.rag.embedding import DefaultEmbeddingFactory
from dbgpt_ext.storage.vector_store.chroma_store import ChromaStore, ChromaVectorConfig
from dbgpt_ext.storage.knowledge_graph.community_summary import CommunitySummaryKnowledgeGraph
from dbgpt_ext.storage.graph_store.tugraph_store import TuGraphStoreConfig
from dbgpt.rag.retriever.embedding import EmbeddingRetriever
from dbgpt_ext.rag.knowledge.factory import KnowledgeFactory
from dbgpt_ext.rag.chunk_manager import ChunkParameters
from dbgpt_ext.rag.assembler import EmbeddingAssembler
from app.core.common.system_env import SystemEnv
from app.core.common.async_func import run_async_function
from dbgpt.rag.retriever import RetrieverStrategy
from app.core.model.knowledge import KnowledgeChunk
from app.plugin.dbgpt.dbgpt_llm_client import DbgptLlmClient

KNOWLEDGE_STORE_PATH = "/knowledge_bases"


class VectorKnowledgeStore(KnowledgeStore):
    """Knowledge base for storing vectors."""

    def __init__(self, name: str):
        config = ChromaVectorConfig(persist_path=SystemEnv.APP_ROOT + KNOWLEDGE_STORE_PATH)
        self._vector_base = ChromaStore(
            config,
            name=name,
            embedding_fn=DefaultEmbeddingFactory.remote(
                api_url=SystemEnv.EMBEDDING_MODEL_API_URL,
                api_key=SystemEnv.EMBEDDING_API_KEY,
                model_name=SystemEnv.EMBEDDING_MODEL_NAME,
            ),
        )
        self._retriever = EmbeddingRetriever(
            top_k=3,
            index_store=self._vector_base,
        )

    def load_document(self, file_path: str, config: Optional[str]) -> str:
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
        return ",".join(chunk_ids)

    def delete_document(self, chunk_ids: str) -> None:
        self._vector_base.delete_by_ids(chunk_ids)

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
        self._vector_base._clean_persist_folder()


class GraphKnowledgeStore(KnowledgeStore):
    """Knowledge base for storing graphs."""

    def __init__(self, name: str):
        config = TuGraphStoreConfig(
            username="admin",
            password="73@TuGraph",
            host="47.76.118.68",
            port="7687",
            enable_summary="True",
        )
        vector_store_config = ChromaVectorConfig(
            persist_path=SystemEnv.APP_ROOT + KNOWLEDGE_STORE_PATH
        )
        self._graph_base = CommunitySummaryKnowledgeGraph(
            config=config,
            name=name,
            embedding_fn=DefaultEmbeddingFactory.remote(
                api_url=SystemEnv.EMBEDDING_MODEL_API_URL,
                api_key=SystemEnv.EMBEDDING_API_KEY,
                model_name=SystemEnv.EMBEDDING_MODEL_NAME,
            ),
            llm_client=DbgptLlmClient()._llm_client,
            kg_document_graph_enabled=True,
            kg_triplet_graph_enabled=True,
            vector_store_config=vector_store_config,
        )
        self._retriever = EmbeddingRetriever(
            top_k=3, index_store=self._graph_base, retrieve_strategy=RetrieverStrategy.GRAPH
        )

    def load_document(self, file_path: str, config: Optional[str]) -> str:
        knowledge = KnowledgeFactory.from_file_path(file_path)
        if config:
            chunk_parameters = ChunkParameters(
                chunk_strategy="CHUNK_BY_SIZE", chunk_size=int(config["chunk_size"])
            )
        else:
            chunk_parameters = ChunkParameters(chunk_strategy="CHUNK_BY_SIZE")
        assembler = EmbeddingAssembler.load_from_knowledge(
            knowledge=knowledge,
            chunk_parameters=chunk_parameters,
            index_store=self._graph_base,
            retrieve_strategy=RetrieverStrategy.GRAPH,
        )
        chunk_ids = run_async_function(assembler.apersist)
        return ",".join(chunk_ids)

    def delete_document(self, chunk_ids: str) -> None:
        self._graph_base.delete_by_ids(chunk_ids)

    def update_document(self, file_path: str, chunk_ids: str) -> str:
        self.delete_document(chunk_ids)
        return run_async_function(self.load_document, file_path=file_path)

    def retrieve(self, query: str) -> List[KnowledgeChunk]:
        chunks = run_async_function(
            self._graph_base.asimilar_search_with_scores, text=query, topk=3, score_threshold=0.3
        )
        knowledge_chunks = [
            KnowledgeChunk(chunk_name=chunk.chunk_name, content=chunk.content) for chunk in chunks
        ]
        return knowledge_chunks

    def drop(self) -> None:
        self._graph_base.delete_vector_name("")
