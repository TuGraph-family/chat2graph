from app.core.model.graph_db_config import GraphDbConfig
from app.core.service.graph_db_service import GraphDbService


class GraphDbWrapper:
    """Facade for graph database operations."""

    def __init__(self, graph_db_config: GraphDbConfig):
        self._graph_db_config = graph_db_config

    def graph_db(self):
        """Get the graph database configuration."""
        graph_db_service: GraphDbService = GraphDbService.instance
        return graph_db_service.create_graph_db(self._graph_db_config)

    # TODO: add more methods for the facade as needed
