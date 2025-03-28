from dataclasses import dataclass
from typing import Optional


@dataclass
class GraphDbConfig:
    """GraphDbConfig class"""

    ip: str
    port: int
    user: str
    pwd: str
    name: str
    id: Optional[str] = None
    desc: str = ""
    is_default_db: bool = True
