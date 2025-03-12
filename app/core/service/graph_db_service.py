from typing import List, Optional

from app.core.common.singleton import Singleton
from app.core.dal.dao.graph_db_dao import GraphDbDao
from app.core.model.graph_db import GraphDB


class GraphDbService(metaclass=Singleton):
    """GraphDB Service"""

    def __init__(self):
        self._graph_db_dao: GraphDbDao = GraphDbDao.instance

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
        result = self._graph_db_dao.create(
            ip=ip, port=port, user=user, pwd=pwd, desc=desc, name=name, is_default_db=is_default_db
        )
        return GraphDB(
            ip=str(result.ip),
            id=str(result.id),
            port=int(result.port),
            user=str(result.user),
            pwd=str(result.pwd),
            desc=str(result.desc),
            name=str(result.name),
            is_default_db=bool(result.is_default_db),
        )

    def get_graph_db(self, id: str) -> GraphDB:
        """Get a GraphDB by ID."""
        result = self._graph_db_dao.get_by_id(id=id)
        if not result:
            raise ValueError(f"GraphDB with ID {id} not found")
        return GraphDB(
            id=str(result.id),
            ip=str(result.ip),
            port=int(result.port),
            user=str(result.user),
            pwd=str(result.pwd),
            desc=str(result.desc),
            name=str(result.name),
            is_default_db=bool(result.is_default_db),
        )

    def delete_graph_db(self, id: str):
        """Delete a GraphDB by ID."""
        graph_db = self._graph_db_dao.get_by_id(id=id)
        if not graph_db:
            raise ValueError(f"GraphDB with ID {id} not found")
        self._graph_db_dao.delete(id=id)

    def update_graph_db(
        self,
        id: str,
        ip: Optional[str] = None,
        port: Optional[int] = None,
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
            port (Optional[int]): New port of the GraphDB
            user (Optional[str]): New user of the GraphDB
            pwd (Optional[str]): New password of the GraphDB
            desc (Optional[str]): New description of the GraphDB
            name (Optional[str]): New name of the GraphDB
            is_default_db (Optional[bool]): New value of is_default_db
        Returns:
            GraphDB: Updated GraphDB object
        """
        graph_db = self._graph_db_dao.get_by_id(id=id)
        if not graph_db:
            raise ValueError(f"GraphDB with ID {id} not found")
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
            updated_graph_db = self._graph_db_dao.update(id=id, **fields_to_update)
            return GraphDB(
                id=str(updated_graph_db.id),
                ip=str(updated_graph_db.ip),
                port=int(updated_graph_db.port),
                user=str(updated_graph_db.user),
                pwd=str(updated_graph_db.pwd),
                desc=str(updated_graph_db.desc),
                name=str(updated_graph_db.name),
                is_default_db=bool(updated_graph_db.is_default_db),
            )
        return GraphDB(
            id=str(graph_db.id),
            ip=str(graph_db.ip),
            port=int(graph_db.port),
            user=str(graph_db.user),
            pwd=str(graph_db.pwd),
            desc=str(graph_db.desc),
            name=str(graph_db.name),
            is_default_db=bool(graph_db.is_default_db),
        )

    def get_all_graph_dbs(self) -> List[GraphDB]:
        """Get all GraphDBs."""

        results = self._graph_db_dao.get_all()
        return [
            GraphDB(
                ip=str(result.ip),
                id=str(result.id),
                port=int(result.port),
                user=str(result.user),
                pwd=str(result.pwd),
                desc=str(result.desc),
                name=str(result.name),
                is_default_db=bool(result.is_default_db),
            )
            for result in results
        ]

    def validate_graph_connection(self, ip: str, port: str, user: str, pwd: str) -> bool:
        """Validate connection to a graph database."""
        raise NotImplementedError("Method not implemented")
