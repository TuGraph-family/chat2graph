from typing import List, Optional

from app.core.common.singleton import Singleton
from app.core.common.system_env import SystemEnv
from app.core.dal.dao.graph_db_dao import GraphDbDao
from app.core.graph_db.graph_db import GraphDb
from app.core.graph_db.graph_db_config import GraphDbConfig
from app.core.graph_db.graph_db_factory import GraphDbFactory


class GraphDbService(metaclass=Singleton):
    """GraphDB Service"""

    def __init__(self):
        self._graph_db_dao: GraphDbDao = GraphDbDao.instance

    def create_graph_db(self, graph_db_config: Optional[GraphDbConfig]) -> GraphDbConfig:
        """Create a new GraphDB."""

        if not graph_db_config:
            graph_db_config = GraphDbConfig(
                type=SystemEnv.GRAPH_DB_TYPE,
                name=SystemEnv.GRAPH_DB_NAME,
                host=SystemEnv.GRAPH_DB_HOST,
                port=SystemEnv.GRAPH_DB_PORT,
                user=SystemEnv.GRAPH_DB_USERNAME,
                pwd=SystemEnv.GRAPH_DB_PASSWORD,
            )

        # determinate default flag
        graph_db_config.is_default_db = self._graph_db_dao.count() == 0

        result = self._graph_db_dao.create(
            type=graph_db_config.type.value,
            name=graph_db_config.name,
            desc=graph_db_config.desc,
            host=graph_db_config.host,
            port=graph_db_config.port,
            user=graph_db_config.user,
            pwd=graph_db_config.pwd,
            is_default_db=graph_db_config.is_default_db,
            default_schema=graph_db_config.default_schema,
        )

        return GraphDbConfig.from_do(result)

    def get_default_graph_db(self) -> GraphDb:
        """Get the default GraphDB."""
        config = self.get_default_graph_db_config()
        return GraphDbFactory.get_graph_db(graph_db_type=config.type, config=config)

    def get_default_graph_db_config(self) -> GraphDbConfig:
        """Get the default GraphDB."""
        graph_db_do = self._graph_db_dao.get_by_default()
        if not graph_db_do:
            raise ValueError("Default GraphDB not found")
        return GraphDbConfig.from_do(graph_db_do)

    def get_graph_db_config(self, id: str) -> GraphDbConfig:
        """Get a GraphDB by ID."""
        graph_db_do = self._graph_db_dao.get_by_id(id=id)
        if not graph_db_do:
            raise ValueError(f"GraphDB with ID {id} not found")
        return GraphDbConfig.from_do(graph_db_do)

    def delete_graph_db(self, id: str) -> None:
        """Delete a GraphDB by ID."""
        graph_db = self._graph_db_dao.get_by_id(id=id)
        if not graph_db:
            raise ValueError(f"GraphDB with ID {id} not found")
        self._graph_db_dao.delete(id=id)

    def update_graph_db_config(self, graph_db_config: GraphDbConfig) -> GraphDbConfig:
        """Update a GraphDB by ID.

        Args:
            graph_db_config (GraphDbConfig): GraphDB configuration

        Returns:
            GraphDB: Updated GraphDB object
        """
        id = graph_db_config.id
        assert id is not None, "ID is required to update a GraphDB"
        graph_db_do = self._graph_db_dao.get_by_id(id=id)
        if not graph_db_do:
            raise ValueError(f"GraphDB with ID {id} not found")

        # check default flag
        if graph_db_do.is_default_db and not graph_db_config.is_default_db:
            raise ValueError("At least one default GraphDB required")

        if not graph_db_do.is_default_db and graph_db_config.is_default_db:
            self._graph_db_dao.set_as_default(id=id)

        update_fields = {
            "type": graph_db_config.type.value if graph_db_config.type else None,
            "name": graph_db_config.name,
            "desc": graph_db_config.desc,
            "host": graph_db_config.host,
            "port": graph_db_config.port,
            "user": graph_db_config.user,
            "pwd": graph_db_config.pwd,
            "is_default_db": graph_db_config.is_default_db,
            "default_schema": graph_db_config.default_schema,
        }

        fields_to_update = {
            field: new_value
            for field, new_value in update_fields.items()
            if new_value is not None and getattr(graph_db_do, field) != new_value
        }

        if fields_to_update:
            assert graph_db_config.id is not None, "ID must be provided for update"
            result = self._graph_db_dao.update(id=graph_db_config.id, **fields_to_update)
            return GraphDbConfig.from_do(result)

        return GraphDbConfig.from_do(graph_db_do)

    def get_all_graph_db_configs(self) -> List[GraphDbConfig]:
        """Get all GraphDBs."""

        results = self._graph_db_dao.get_all()
        return [GraphDbConfig.from_do(result) for result in results]

    def validate_graph_db_connection(self, graph_db_config: GraphDbConfig) -> bool:
        """Validate connection to a graph database."""
        raise NotImplementedError("Method not implemented")
