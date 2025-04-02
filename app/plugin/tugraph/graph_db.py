from neo4j import GraphDatabase

from app.core.graph_db.graph_db import GraphDb
from app.core.graph_db.graph_db_config import TuGraphDbConfig


class TuGraphDb(GraphDb[TuGraphDbConfig]):
    """Graph store implementation for TuGraph database."""

    def __init__(self, config: TuGraphDbConfig):
        super().__init__(config=config)

    @property
    def conn(self):
        """Get the database connection."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self._config.uri, auth=(self._config.user, self._config.pwd)
            )
        return self._driver
