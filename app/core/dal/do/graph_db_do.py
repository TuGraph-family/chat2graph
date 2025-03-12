from uuid import uuid4

from sqlalchemy import Boolean, Column, String, Text

from app.core.dal.database import Do


class GraphDbDo(Do):  # type: ignore
    """GraphDB to store graph database details."""

    __tablename__ = "graph_db"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ip = Column(Text, nullable=False)
    port = Column(Text, nullable=False)
    user = Column(Text, nullable=False)
    pwd = Column(Text, nullable=False)
    desc = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    is_default_db = Column(Boolean, nullable=False)
