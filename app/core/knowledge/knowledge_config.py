from dataclasses import dataclass


@dataclass
class KnowledgeConfig:
    """Knowledge loading configuration."""

    chunk_size: int = 512
