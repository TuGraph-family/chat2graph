from typing import Optional

from neo4j import GraphDatabase

from app.core.common.system_env import SystemEnv
from app.core.graph_db.graph_db import GraphDb
from app.core.graph_db.graph_db_config import Neo4jDbConfig  # type: ignore


class Neo4jDb(GraphDb):
    """Graph store implementation."""

    def __init__(self, config: Neo4jDbConfig):
        """Initialize Neo4j store with configuration."""
        super().__init__(config=config)

    @property
    def conn(self):
        """Get the database connection."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self.config.uri, auth=(self.config.user, self.config.pwd)
            )
        return self._driver


def get_graph_db(config: Optional[Neo4jDbConfig] = None) -> Neo4jDb:
    """Initialize neo4j store with configuration."""
    try:
        config = config or Neo4jDbConfig(
            type=SystemEnv.GRAPH_DB_TYPE,
            name=SystemEnv.GRAPH_DB_NAME,
            host=SystemEnv.GRAPH_DB_HOST,
            port=SystemEnv.GRAPH_DB_PORT,
            user=SystemEnv.GRAPH_DB_USERNAME,
            pwd=SystemEnv.GRAPH_DB_PASSWORD,
        )
        store = Neo4jDb(config)
        print(f"[log] get graph: {config.name}")

        return store

    except Exception as e:
        print(f"Failed to initialize neo4j: {str(e)}")
        raise
