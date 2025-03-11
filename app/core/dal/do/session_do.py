from uuid import uuid4

from sqlalchemy import BigInteger, Column, String

from app.core.common.util import utc_now
from app.core.dal.database import Base


class SessionDo(Base):  # type: ignore
    """Session to store session details."""

    __tablename__ = "session"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(BigInteger, default=utc_now, nullable=False)
    name = Column(String(80), nullable=True)
