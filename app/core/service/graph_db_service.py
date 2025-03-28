from typing import List

from app.core.common.singleton import Singleton
from app.core.dal.dao.graph_db_dao import GraphDbDao
from app.core.model.graph_db import GraphDbConfig


class GraphDbService(metaclass=Singleton):
    """GraphDB Service"""

    def __init__(self):
        self._graph_db_dao: GraphDbDao = GraphDbDao.instance

    def create_graph_db(self, graph_db_config: GraphDbConfig) -> GraphDbConfig:
        """Create a new GraphDB."""

        # determinate default flag
        graph_db_config.is_default_db = self._graph_db_dao.count() == 0

        result = self._graph_db_dao.create(
            port=graph_db_config.port,
            user=graph_db_config.user,
            pwd=graph_db_config.pwd,
            desc=graph_db_config.desc,
            name=graph_db_config.name,
            is_default_db=graph_db_config.is_default_db,
        )

        return GraphDbConfig(
            ip=str(result.ip),
            id=str(result.id),
            port=int(result.port),
            user=str(result.user),
            pwd=str(result.pwd),
            desc=str(result.desc),
            name=str(result.name),
            is_default_db=bool(result.is_default_db),
        )

    def get_default_graph_db(self) -> GraphDbConfig:
        """Get the default GraphDB."""
        graph_db_do = self._graph_db_dao.get_by_default()
        if not graph_db_do:
            raise ValueError("Default GraphDB not found")
        return GraphDbConfig(
            id=str(graph_db_do.id),
            ip=str(graph_db_do.ip),
            port=int(graph_db_do.port),
            user=str(graph_db_do.user),
            pwd=str(graph_db_do.pwd),
            desc=str(graph_db_do.desc),
            name=str(graph_db_do.name),
            is_default_db=bool(graph_db_do.is_default_db),
        )

    def get_graph_db(self, id: str) -> GraphDbConfig:
        """Get a GraphDB by ID."""
        graph_db_do = self._graph_db_dao.get_by_id(id=id)
        if not graph_db_do:
            raise ValueError(f"GraphDB with ID {id} not found")
        return GraphDbConfig(
            id=str(graph_db_do.id),
            ip=str(graph_db_do.ip),
            port=int(graph_db_do.port),
            user=str(graph_db_do.user),
            pwd=str(graph_db_do.pwd),
            desc=str(graph_db_do.desc),
            name=str(graph_db_do.name),
            is_default_db=bool(graph_db_do.is_default_db),
        )

    def delete_graph_db(self, id: str):
        """Delete a GraphDB by ID."""
        graph_db = self._graph_db_dao.get_by_id(id=id)
        if not graph_db:
            raise ValueError(f"GraphDB with ID {id} not found")
        self._graph_db_dao.delete(id=id)

    def update_graph_db(self, graph_db_config: GraphDbConfig) -> GraphDbConfig:
        """Update a GraphDB by ID.

        Args:
            graph_db_config (GraphDbConfig): GraphDB configuration

        Returns:
            GraphDB: Updated GraphDB object
        """
        assert graph_db_config.id is not None, "ID is required to update a GraphDB"
        graph_db_do = self._graph_db_dao.get_by_id(id=graph_db_config.id)
        if not graph_db_do:
            raise ValueError(f"GraphDB with ID {id} not found")

        # check default flag
        if graph_db.is_default_db and not is_default_db:
            raise ValueError(f"At least one default GraphDB required")

        if not graph_db.is_default_db and is_default_db:
            self._graph_db_dao.set_as_default(id=id)

        update_fields = {
            "ip": graph_db_config.ip,
            "port": graph_db_config.port,
            "user": graph_db_config.user,
            "pwd": graph_db_config.pwd,
            "desc": graph_db_config.desc,
            "name": graph_db_config.name,
            "is_default_db": graph_db_config.is_default_db,
        }

        fields_to_update = {
            field: new_value
            for field, new_value in update_fields.items()
            if new_value is not None and getattr(graph_db_do, field) != new_value
        }

        if fields_to_update:
            updated_graph_db = self._graph_db_dao.update(id=graph_db_config.id, **fields_to_update)
            return GraphDbConfig(
                id=str(updated_graph_db.id),
                ip=str(updated_graph_db.ip),
                port=int(updated_graph_db.port),
                user=str(updated_graph_db.user),
                pwd=str(updated_graph_db.pwd),
                desc=str(updated_graph_db.desc),
                name=str(updated_graph_db.name),
                is_default_db=bool(updated_graph_db.is_default_db),
            )
        return GraphDbConfig(
            id=str(graph_db_do.id),
            ip=str(graph_db_do.ip),
            port=int(graph_db_do.port),
            user=str(graph_db_do.user),
            pwd=str(graph_db_do.pwd),
            desc=str(graph_db_do.desc),
            name=str(graph_db_do.name),
            is_default_db=bool(graph_db_do.is_default_db),
        )

    def get_all_graph_dbs(self) -> List[GraphDbConfig]:
        """Get all GraphDBs."""

        results = self._graph_db_dao.get_all()
        return [
            GraphDbConfig(
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

    def validate_graph_db_connection(self, graph_db_config: GraphDbConfig) -> bool:
        """Validate connection to a graph database."""
        raise NotImplementedError("Method not implemented")
