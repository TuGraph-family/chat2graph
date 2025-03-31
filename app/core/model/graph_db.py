from dataclasses import dataclass, asdict
from typing import Optional

from app.core.common.type import GraphDbType
from app.core.dal.do.graph_db_do import GraphDbDo


@dataclass
class GraphDbConfig:
    """GraphDbConfig class"""
    type: GraphDbType
    name: str
    ip: str
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
    def from_do(do: GraphDbDo):
        return GraphDbConfig(
            id=do.id,
            create_time=do.create_time,
            update_time=do.update_time,
            type=GraphDbType(do.type),
            name=do.name,
            desc=do.desc,
            ip=do.ip,
            port=int(do.port),
            user=do.user,
            pwd=do.pwd,
            default_schema=do.default_schema,
            is_default_db=bool(do.is_default_db),
        )

    def to_dict(self):
        """Convert to dictionary"""
        data = asdict(self)
        data["type"] = data["type"].value
        return data


class Neo4jDbConfig(GraphDbConfig):
    """Neo4jDbConfig class"""

    @property
    def uri(self) -> str:
        """Get the connection URI."""
        return f"bolt://{self.ip}:{self.port}"
