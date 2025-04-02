from app.core.common.type import GraphDbType
from app.core.graph_db.graph_db import GraphDb
from app.core.graph_db.graph_db_config import GraphDbConfig, Neo4jDbConfig


class GraphDbFactory:
    """Graph store factory."""

    @staticmethod
    def get_graph_db(graph_db_type: GraphDbType, config: GraphDbConfig) -> GraphDb:
        """Initialize graph store with configuration."""
        if graph_db_type == GraphDbType.NEO4J:
            if not isinstance(config, Neo4jDbConfig):
                raise ValueError("config must be Neo4jDbConfig for Neo4j graph db")
            from app.plugin.neo4j.graph_store import Neo4jDb

            return Neo4jDb(config)

        # TODO: add other graph db types here, GraphDbType.TUGRAPH

        raise ValueError(f"Unsupported graph database type: {graph_db_type}")
