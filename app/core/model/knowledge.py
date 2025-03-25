from dataclasses import dataclass
from typing import List

from app.core.prompt.knowledge import KNOWLEDGE_PROMPT


@dataclass
class KnowledgeChunk:
    """Knowledge Chunk class"""

    chunk_name: str
    content: str


@dataclass
class Knowledge:
    """Knowledge"""

    global_chunks: List[KnowledgeChunk]
    local_chunks: List[KnowledgeChunk]

    def get_payload(self) -> str:
        """Get the content of the knowledge."""
        global_knowledges = ""
        for chunk in self.global_chunks:
            global_knowledges += f"chunk_name:{chunk.chunk_name}\n"
            global_knowledges += f"content:{chunk.content}\n"
            global_knowledges += "\n"
        local_knowledges = ""
        for chunk in self.local_chunks:
            local_knowledges += f"chunk_name:{chunk.chunk_name}\n"
            local_knowledges += f"content:{chunk.content}\n"
            local_knowledges += "\n"
        self._payload = KNOWLEDGE_PROMPT.format(
            global_knowledges=global_knowledges, local_knowledges=local_knowledges
        )
        return self._payload
