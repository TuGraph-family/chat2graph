from typing import Any, Dict, List, Optional, Tuple

from app.core.service.graph_db_service import GraphDbService
from app.server.common.util import ServiceException


class GraphDBManager:
    """GraphDB Manager class to handle business logic"""

    def __init__(self):
        self._graph_db_service: GraphDbService = GraphDbService.instance

    def create_graph_db(
        self, ip: str, port: str, user: str, pwd: str, desc: str, name: str, is_default_db: bool
    ) -> Tuple[Dict[str, Any], str]:
        """
        Create a new GraphDB and return the response data.

        Args:
            ip (str): IP address of the GraphDB
            port (str): Port of the GraphDB
            user (str): Username for the GraphDB
            pwd (str): Password for the GraphDB
            desc (str): Description of the GraphDB
            name (str): Name of the GraphDB
            is_default_db (bool): Whether this GraphDB is the default database

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing GraphDB details and success message
        """
        try:
            graph_db = self._graph_db_service.create_graph_db(
                ip=ip,
                port=port,
                user=user,
                pwd=pwd,
                desc=desc,
                name=name,
                is_default_db=is_default_db,
            )
            data = {
                "id": graph_db.id,
                "ip": graph_db.ip,
                "port": graph_db.port,
                "user": graph_db.user,
                "pwd": graph_db.pwd,
                "desc": graph_db.desc,
                "name": graph_db.name,
                "is_default_db": graph_db.is_default_db,
            }
            return data, "GraphDB created successfully"
        except Exception as e:
            raise ServiceException(f"Failed to create GraphDB: {str(e)}") from e

    def get_graph_db(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Get GraphDB details by ID.

        Args:
            id (str): ID of the GraphDB

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing GraphDB details and success message
        """
        try:
            graph_db = self._graph_db_service.get_graph_db(id=id)
            data = {
                "id": graph_db.id,
                "ip": graph_db.ip,
                "port": graph_db.port,
                "user": graph_db.user,
                "pwd": graph_db.pwd,
                "desc": graph_db.desc,
                "name": graph_db.name,
                "is_default_db": graph_db.is_default_db,
            }
            return data, "GraphDB fetched successfully"
        except Exception as e:
            raise ServiceException(f"Failed to fetch GraphDB: {str(e)}") from e

    def delete_graph_db(self, id: str) -> Tuple[Dict[str, Any], str]:
        """Delete a GraphDB by ID.

        Args:
            id (str): ID of the GraphDB

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing deletion status and success message
        """
        try:
            self._graph_db_service.delete_graph_db(id=id)
            return {}, f"GraphDB with ID {id} deleted successfully"
        except Exception as e:
            raise ServiceException(f"Failed to delete GraphDB: {str(e)}") from e

    def update_graph_db(
        self,
        id: str,
        ip: Optional[str] = None,
        port: Optional[str] = None,
        user: Optional[str] = None,
        pwd: Optional[str] = None,
        desc: Optional[str] = None,
        name: Optional[str] = None,
        is_default_db: Optional[bool] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Update a GraphDB's details by ID.

        Args:
            id (str): ID of the GraphDB
            ip (Optional[str]): New IP address for the GraphDB
            port (Optional[str]): New port for the GraphDB
            user (Optional[str]): New username for the GraphDB
            pwd (Optional[str]): New password for the GraphDB
            desc (Optional[str]): New description for the GraphDB
            name (Optional[str]): New name for the GraphDB
            is_default_db (Optional[bool]): New value for is_default_db

        Returns:
            Tuple[Dict[str, Any], str]: A tuple containing updated GraphDB details and success
                message
        """
        try:
            graph_db = self._graph_db_service.update_graph_db(
                id=id,
                ip=ip,
                port=port,
                user=user,
                pwd=pwd,
                desc=desc,
                name=name,
                is_default_db=is_default_db,
            )
            data = {
                "id": graph_db.id,
                "ip": graph_db.ip,
                "port": graph_db.port,
                "user": graph_db.user,
                "pwd": graph_db.pwd,
                "desc": graph_db.desc,
                "name": graph_db.name,
                "is_default_db": graph_db.is_default_db,
            }
            return data, "GraphDB updated successfully"
        except Exception as e:
            raise ServiceException(f"Failed to update GraphDB: {str(e)}") from e

    def get_all_graph_dbs(self) -> Tuple[List[dict], str]:
        """Get all GraphDBs.

        Returns:
            Tuple[List[dict], str]: A tuple containing a list of GraphDB details and success message
        """
        try:
            graph_dbs = self._graph_db_service.get_all_graph_dbs()
            graph_db_list = [
                {
                    "id": graph_db.id,
                    "ip": graph_db.ip,
                    "port": graph_db.port,
                    "user": graph_db.user,
                    "pwd": graph_db.pwd,
                    "desc": graph_db.desc,
                    "name": graph_db.name,
                    "is_default_db": graph_db.is_default_db,
                }
                for graph_db in graph_dbs
            ]
            return graph_db_list, "Get all GraphDBs successfully"
        except Exception as e:
            raise ServiceException(f"Failed to fetch all GraphDBs: {str(e)}") from e

    def validate_graph_connection(
        self, ip: str, port: str, user: str, pwd: str
    ) -> Tuple[bool, str]:
        """Validate connection to a GraphDB.

        Args:
            ip (str): IP address of the GraphDB
            port (str): Port of the GraphDB
            user (str): Username for the GraphDB
            pwd (str): Password for the GraphDB

        Returns:
            Tuple[bool, str]: A tuple containing validation result and success/failure message
        """
        try:
            is_valid = self._graph_db_service.validate_graph_connection(
                ip=ip, port=port, user=user, pwd=pwd
            )

            if is_valid:
                return True, "GraphDB connection validated successfully"
            return False, "GraphDB connection validation failed"
        except Exception as e:
            raise ServiceException(f"Failed to validate GraphDB connection: {str(e)}") from e
