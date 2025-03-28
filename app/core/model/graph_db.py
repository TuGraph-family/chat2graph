from dataclasses import dataclass
from typing import Optional


@dataclass
class GraphDbConfig:
    """GraphDbConfig class"""

    ip: str
    port: int
    name: str
    user: str
    pwd: str
    id: Optional[str] = None
    desc: str = ""
    is_default_db: bool = True


class Neo4jDbConfig(GraphDbConfig):
    """Neo4jDbConfig class"""

    @property
    def uri(self) -> str:
        """Get the connection URI."""
        return f"bolt://{self.ip}:{self.port}"
