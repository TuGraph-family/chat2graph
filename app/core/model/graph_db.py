from dataclasses import dataclass


@dataclass
class GraphDB:
    """GraphDB class"""

    id: str
    ip: str
    port: int
    user: str
    pwd: str
    desc: str
    name: str
    is_default_db: bool
