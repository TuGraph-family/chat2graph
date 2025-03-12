from uuid import uuid4

from sqlalchemy import Boolean, Column, Integer, String, Text

from app.core.dal.database import Do


class GraphDbDo(Do):  # type: ignore
    """GraphDB to store graph database details."""

    __tablename__ = "graph_db"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ip = Column(String(45), nullable=False)  # IPv6 max length is 45 chars
    port = Column(Integer, nullable=False)
    user = Column(String(36), nullable=False)
    pwd = Column(String(36), nullable=False)
    desc = Column(Text, nullable=False)
    name = Column(String(36), nullable=False)
    is_default_db = Column(Boolean, nullable=False)
