from app.core.common.type import GraphDbType
from app.core.model.graph_db_config import GraphDbConfig, Neo4jDbConfig, TuGraphDbConfig
from app.core.toolkit.graph_db.graph_db import GraphDb


class GraphDbFactory:
    """Graph store factory."""

    @staticmethod
    def get_graph_db(graph_db_type: GraphDbType, config: GraphDbConfig) -> GraphDb:
        """Initialize graph store with configuration."""
        if graph_db_type == GraphDbType.NEO4J:
            if not isinstance(config, Neo4jDbConfig):
                raise ValueError("config must be Neo4jDbConfig for Neo4j graph db")
            from app.plugin.neo4j.graph_db import Neo4jDb

            return Neo4jDb(config)

        if graph_db_type == GraphDbType.TUGRAPH:
            if not isinstance(config, TuGraphDbConfig):
                raise ValueError("config must be TuGraphDbConfig for TuGraph graph db")
            from app.plugin.tugraph.graph_db import TuGraphDb  # type: ignore

            return TuGraphDb(config)

        raise ValueError(f"Unsupported graph database type: {graph_db_type}")
