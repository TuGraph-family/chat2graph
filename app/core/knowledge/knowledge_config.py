from dataclasses import dataclass


@dataclass
class KnowledgeConfig:
    """Knowledge loading configuration."""

    chunk_size: int = 512

    def to_dict(self):
        """Convert to dict."""
        return self.__dict__
