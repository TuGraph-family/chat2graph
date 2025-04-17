from dataclasses import asdict, dataclass
import json
from typing import Any, Dict, Optional, cast

from app.core.common.type import GraphDbType
from app.core.dal.do.graph_db_do import GraphDbDo


@dataclass
class GraphDbConfig:
    """GraphDbConfig class"""

    type: GraphDbType
    name: str
    host: str
    port: int
    id: Optional[str] = None
    create_time: Optional[int] = None
    update_time: Optional[int] = None
    desc: Optional[str] = None
    user: Optional[str] = None
    pwd: Optional[str] = None
    default_schema: Optional[str] = None
    is_default_db: bool = False

    @staticmethod
    def from_do(do: GraphDbDo) -> "GraphDbConfig":
        """Create a GraphDbConfig instance from a GraphDbDo object."""
        if str(do.type) == GraphDbType.NEO4J.value:
            return Neo4jDbConfig.from_do(do)
        return GraphDbConfig(
            id=str(do.id),
            create_time=int(do.create_time),
            update_time=int(do.update_time),
            type=GraphDbType(do.type),
            name=str(do.name),
            desc=cast(str, do.desc),
            host=str(do.host),
            port=int(do.port),
            user=cast(str, do.user),
            pwd=cast(str, do.pwd),
            default_schema=cast(str, do.default_schema),
            is_default_db=bool(do.is_default_db),
        )

    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        data["type"] = data["type"].value
        return data


@dataclass
class Neo4jDbConfig(GraphDbConfig):
    """Neo4jDbConfig class"""

    schema_metadata: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_do(do: GraphDbDo) -> "Neo4jDbConfig":
        return Neo4jDbConfig(
            id=str(do.id),
            create_time=int(do.create_time),
            update_time=int(do.update_time),
            type=GraphDbType(do.type),
            name=str(do.name),
            desc=cast(str, do.desc),
            host=str(do.host),
            port=int(do.port),
            user=cast(str, do.user),
            pwd=cast(str, do.pwd),
            default_schema=cast(str, do.default_schema),
            is_default_db=bool(do.is_default_db),
            schema_metadata=json.loads(str(do.schema_metadata))
            if do.schema_metadata
            else {
                "nodes": {},
                "relationships": {},
            },
        )

    @property
    def uri(self) -> str:
        """Get the connection URI."""
        return f"bolt://{self.host}:{self.port}"


class TuGraphDbConfig(GraphDbConfig):
    """TuGraphDbConfig class"""

    @property
    def uri(self) -> str:
        """Get the connection URI for TuGraph."""
        return f"bolt://{self.host}:{self.port}"
