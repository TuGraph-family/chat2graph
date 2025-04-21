from typing import Optional
from uuid import uuid4

from app.core.model.graph_db_config import GraphDbConfig
from app.core.service.graph_db_service import GraphDbService
from app.core.toolkit.tool import Tool


class SystemStatusChecker(Tool):
    """Tool for checking the system status."""

    def __init__(self, id: Optional[str] = None):
        super().__init__(
            id=id or str(uuid4()),
            name=self.query_system_status.__name__,
            description=self.query_system_status.__doc__ or "",
            function=self.query_system_status,
        )

    async def query_system_status(self, graph_db_service: GraphDbService) -> str:
        """Query the system status.

        Args:
            None

        Returns:
            str: A natural language description of the system status.
        """
        response: str = "Starting to check the system status...\n"

        # graph db connection status
        try:
            graph_db_config: GraphDbConfig = graph_db_service.get_default_graph_db_config()
            is_connected = graph_db_service.validate_graph_db_connection(graph_db_config)
        except ValueError:
            is_connected = False

        if is_connected:
            response += (
                "- The graph database connection is valid.\n"
                f"\tGraph DB name: {graph_db_config.name}\n"
                f"\tGraph DB type: {graph_db_config.type.value}\n"
                f"\tGraph DB host: {graph_db_config.host}\n"
                f"\tGraph DB port: {graph_db_config.port}\n"
                f"\tIs default Graph DB: {graph_db_config.is_default_db}\n"
            )
        else:
            response += (
                "- The graph database connection is invalid. "
                "Please configure the Graph DB configuration and "
                "connect the Graph DB to the system.\n"
            )

        # schema status
        has_schema: bool = False
        if is_connected:
            schema = graph_db_service.get_schema_metadata(
                graph_db_config=graph_db_service.get_default_graph_db_config()
            )

            # count the number of node and relationship types
            node_count = len(schema["nodes"])
            rel_count = len(schema["relationships"])

            if node_count > 0 and rel_count > 0:
                nodes = list(schema.get("nodes", {}).keys())
                relationships = list(schema.get("relationships", {}).keys())
                response += (
                    "- The graph database has established a schema. "
                    f"The current schema includes {node_count} types of node "
                    f"and {rel_count} types of relationship.The schema is as follows:\n"
                    f"\tNodes: {nodes}\n\tRelationships: {relationships}\n"
                )
                has_schema = True
        if not has_schema:
            response += "- The graph database currently does not define a schema.\n"

        response += "System status check completed."
        return response
