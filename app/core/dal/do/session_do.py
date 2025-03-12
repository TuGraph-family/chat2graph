from uuid import uuid4

from sqlalchemy import BigInteger, Column, String, func

from app.core.dal.database import Do


class SessionDo(Do):  # type: ignore
    """Session to store session details."""

    __tablename__ = "session"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(BigInteger, server_default=func.strftime("%s", "now"))
    name = Column(String(80), nullable=True)
