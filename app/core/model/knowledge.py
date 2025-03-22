from app.core.model.message import Message
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

KNOWLEDGE_PROMPT = """
All related knowledges retrieved from the knowledge base are listed below.

[Knowledges From Gloabal Knowledge Base]:
{global_knowledges}

[Knowledges From Local Knowledge Base]:
{local_knowledges}
"""

@dataclass
class KnowledgeChunk:
    """Knowledge Chunk class"""

    chunk_name: str
    content: str



class Knowledge():
    """Knowledge"""

    def __init__(
        self,
        global_chunks: List[KnowledgeChunk],
        local_chunks: List[KnowledgeChunk],
    ):
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
            global_chunk_list=self._global_chunk_list,
            local_chunk_list=self._local_chunk_list,
        )
