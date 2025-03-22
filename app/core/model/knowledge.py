from app.core.model.message import Message
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from app.core.prompt.knowledge import KNOWLEDGE_PROMPT


@dataclass
class KnowledgeChunk:
    """Knowledge Chunk class"""

    chunk_name: str
    content: str


class Knowledge:
    """Knowledge"""

    def __init__(
        self,
        global_chunks: List[KnowledgeChunk],
        local_chunks: List[KnowledgeChunk],
    ):
        self._global_chunks = global_chunks
        self._local_chunks = local_chunks
        global_knowledges = ""
        for chunk in global_chunks:
            global_knowledges += f"chunk_name:{chunk.chunk_name}\n"
            global_knowledges += f"content:{chunk.content}\n"
            global_knowledges += "\n"
        local_knowledges = ""
        for chunk in local_chunks:
            local_knowledges += f"chunk_name:{chunk.chunk_name}\n"
            local_knowledges += f"content:{chunk.content}\n"
            local_knowledges += "\n"
        self._payload = KNOWLEDGE_PROMPT.format(
            global_knowledges=global_knowledges, local_knowledges=local_knowledges
        )

    def get_payload(self) -> str:
        """Get the content of the knowledge."""
        return self._payload

    def copy(self) -> Any:
        """Copy the knowledge."""
        return Knowledge(
            global_chunks=self._global_chunks,
            local_chunks=self._local_chunks,
        )
