from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import relationship

from app.core.common.util import utc_now
from app.core.dal.database import Base


class SessionModel(Base):
    """Session to store session details."""

    __tablename__ = "session"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=utc_now, nullable=False)
    name = Column(String(80), nullable=True)

    messages = relationship("MessageModel", backref="session", cascade="all, delete-orphan")
    knowledge_bases = relationship(
        "KnowledgeBaseModel", backref="session", cascade="all, delete-orphan"
    )
