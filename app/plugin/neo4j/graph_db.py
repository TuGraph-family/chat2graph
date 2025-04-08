from neo4j import GraphDatabase

from app.core.toolkit.graph_db.graph_db import GraphDb
from app.core.model.graph_db_config import Neo4jDbConfig  # type: ignore


class Neo4jDb(GraphDb[Neo4jDbConfig]):
    """Graph store implementation."""

    def __init__(self, config: Neo4jDbConfig):
        super().__init__(config=config)

    @property
    def conn(self):
        """Get the database connection."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self._config.uri, auth=(self._config.user, self._config.pwd)
            )
        return self._driver
