from typing import Any, Dict, List, Optional

from app.core.common.singleton import Singleton
from app.core.dal.dao import GraphDbDAO
from app.core.dal.database import DB
from app.core.model.graph_db import GraphDB
from app.server.common.util import ServiceException


class GraphDbService(metaclass=Singleton):
    """GraphDB Service"""

    def __init__(self):
        self._graph_dbs: Dict[str, Any] = {}
        self._dao = GraphDbDAO(DB())

    def create_graph_db(
        self, ip: str, port: str, user: str, pwd: str, desc: str, name: str, is_default_db: bool
    ) -> GraphDB:
        """Create a new GraphDB.

        Args:
            ip (str): Ip of the GraphDB
            port (str): Port of the GraphDB
            user (str): Username for the GraphDB
            pwd (str): Password for the GraphDB
            desc (str): Description of the GraphDB
            name (str): Name of the GraphDB
            is_default_db (bool): Whether this GraphDB is the default database

        Returns:
            GraphDB: GraphDB object
        """
        # create the GraphDB
        result = self._dao.create(
            ip=ip, port=port, user=user, pwd=pwd, desc=desc, name=name, is_default_db=is_default_db
        )
        return GraphDB(
            ip=result.ip,
            id=result.id,
            port=result.port,
            user=result.user,
            pwd=result.pwd,
            desc=result.desc,
            name=result.name,
            is_default_db=result.is_default_db,
        )

    def get_graph_db(self, id: str) -> GraphDB:
        """Get a GraphDB by ID."""
        result = self._dao.get_by_id(id=id)
        if not result:
            raise ServiceException(f"GraphDB with ID {id} not found")
        return GraphDB(
            id=result.id,
            ip=result.ip,
            port=result.port,
            user=result.user,
            pwd=result.pwd,
            desc=result.desc,
            name=result.name,
            is_default_db=result.is_default_db,
        )

    def delete_graph_db(self, id: str):
        """Delete a GraphDB by ID."""
        graph_db = self._dao.get_by_id(id=id)
        if not graph_db:
            raise ServiceException(f"GraphDB with ID {id} not found")
        self._dao.delete(id=id)

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
    ) -> GraphDB:
        """Update a GraphDB by ID.

        Args:
            id (str): ID of the GraphDB
            ip (Optional[str]): New IP of the GraphDB
            port (Optional[str]): New port of the GraphDB
            user (Optional[str]): New user of the GraphDB
            pwd (Optional[str]): New password of the GraphDB
            desc (Optional[str]): New description of the GraphDB
            name (Optional[str]): New name of the GraphDB
            is_default_db (Optional[bool]): New value of is_default_db
        Returns:
            GraphDB: Updated GraphDB object
        """
        graph_db = self._dao.get_by_id(id=id)
        if not graph_db:
            raise ServiceException(f"GraphDB with ID {id} not found")
        update_fields = {
            "ip": ip,
            "port": port,
            "user": user,
            "pwd": pwd,
            "desc": desc,
            "name": name,
            "is_default_db": is_default_db,
        }

        fields_to_update = {
            field: new_value
            for field, new_value in update_fields.items()
            if new_value is not None and getattr(graph_db, field) != new_value
        }

        if fields_to_update:
            updated_graph_db = self._dao.update(id=id, **fields_to_update)
            return GraphDB(
                id=updated_graph_db.id,
                ip=updated_graph_db.ip,
                port=updated_graph_db.port,
                user=updated_graph_db.user,
                pwd=updated_graph_db.pwd,
                desc=updated_graph_db.desc,
                name=updated_graph_db.name,
                is_default_db=updated_graph_db.is_default_db,
            )
        return GraphDB(
            id=graph_db.id,
            ip=graph_db.ip,
            port=graph_db.port,
            user=graph_db.user,
            pwd=graph_db.pwd,
            desc=graph_db.desc,
            name=graph_db.name,
            is_default_db=graph_db.is_default_db,
        )

    def get_all_graph_dbs(self) -> List[GraphDB]:
        """Get all GraphDBs."""

        results = self._dao.get_all()
        return [
            GraphDB(
                ip=result.ip,
                id=result.id,
                port=result.port,
                user=result.user,
                pwd=result.pwd,
                desc=result.desc,
                name=result.name,
                is_default_db=result.is_default_db,
            )
            for result in results
        ]

    def validate_graph_connection(self, ip: str, port: str, user: str, pwd: str) -> bool:
        """Validate connection to a graph database."""
