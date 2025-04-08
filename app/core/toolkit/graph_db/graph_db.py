from typing import Generic, TypeVar

from app.core.model.graph_db_config import GraphDbConfig

T = TypeVar("T", bound=GraphDbConfig)


class GraphDb(Generic[T]):
    """Graph store implementation."""

    def __init__(self, config: T):
        self._config: T = config
        self._driver = None

    @property
    def conn(self):
        """Get the database connection."""
        raise NotImplementedError("Subclasses should implement this method.")
