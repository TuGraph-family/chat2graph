from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column, Integer, String, Text, func

from app.core.dal.database import Do


class GraphDbDo(Do):  # type: ignore
    """GraphDB to store graph database details."""

    __tablename__ = "graph_db"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    type = Column(String(36), nullable=False)
    name = Column(String(36), nullable=False)
    desc = Column(Text, nullable=True)
    host = Column(String(128), nullable=False)
    port = Column(Integer, nullable=False)
    user = Column(String(36), nullable=True)
    pwd = Column(String(36), nullable=True)
    default_schema = Column(String(36), nullable=True)
    is_default_db = Column(Boolean, nullable=False, default=False)
    create_time = Column(BigInteger, server_default=func.strftime("%s", "now"))
    update_time = Column(
        BigInteger,
        server_default=func.strftime("%s", "now"),
        onupdate=func.strftime("%s", "now"),
    )
