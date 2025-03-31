from typing import Any, Dict, List, Tuple

from app.core.model.graph_db import GraphDbConfig
from app.core.service.graph_db_service import GraphDbService


class GraphDBManager:
    """GraphDB Manager class to handle business logic"""

    def __init__(self):
        self._graph_db_service: GraphDbService = GraphDbService.instance

    def create_graph_db(self, graph_db_config: GraphDbConfig) -> Tuple[Dict[str, Any], str]:
        """Create a new GraphDB and return the response data.

        Args:
            graph_db_config (GraphDbConfig): GraphDB configuration

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing GraphDB details and success message
        """
        graph_db = self._graph_db_service.create_graph_db(graph_db_config=graph_db_config)
        return graph_db.to_dict(), "GraphDB created successfully"

    def get_graph_db(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Get GraphDB details by ID.

        Args:
            id (str): ID of the GraphDB

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing GraphDB details and success message
        """
        graph_db = self._graph_db_service.get_graph_db(id=id)
        return graph_db.to_dict(), "GraphDB fetched successfully"

    def delete_graph_db(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Delete a GraphDB by ID.

        Args:
            id (str): ID of the GraphDB

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        self._graph_db_service.delete_graph_db(id=id)
        return {}, f"GraphDB with ID {id} deleted successfully"

    def update_graph_db(self, graph_db_config: GraphDbConfig) -> Tuple[Dict[str, Any], str]:
        """Update a GraphDB's details by ID.

        Args:
            graph_db_config (GraphDbConfig): GraphDB configuration

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing updated GraphDB details and success
                message
        """
        graph_db = self._graph_db_service.update_graph_db(graph_db_config=graph_db_config)
        return graph_db.to_dict(), "GraphDB updated successfully"

    def get_all_graph_db_configs(self) -> Tuple[List[dict], str]:
        """Get all GraphDBs.

        Returns:
            Tuple[List[dict], str]: A tuple containing a list of GraphDB details and success message
        """
        graph_db_configs = self._graph_db_service.get_all_graph_dbs()
        graph_db_list = [
            graph_db.to_dict()
            for graph_db in graph_db_configs
        ]
        return graph_db_list, "Get all GraphDBs successfully"

    def validate_graph_db_connection(self, graph_db_config: GraphDbConfig) -> Tuple[bool, str]:
        """Validate connection to a GraphDB.

        Args:
            graph_db_config (GraphDbConfig): GraphDB configuration

        Returns:
            Tuple[bool, str]: A tuple containing validation result and success/failure message
        """
        is_valid = self._graph_db_service.validate_graph_db_connection(
            graph_db_config=graph_db_config
        )

        if is_valid:
            return True, "GraphDB connection validated successfully"
        return False, "GraphDB connection validation failed"
