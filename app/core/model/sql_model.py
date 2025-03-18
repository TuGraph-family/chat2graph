from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.dal.database import Base


def utc_now():
    """Get the current time in UTC."""
    return datetime.now()


class Session(Base):
    """Session to store session details."""

    __tablename__ = "session"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=utc_now, nullable=False)
    name = Column(String(80), nullable=True)

    messages = relationship("Message", backref="session", cascade="all, delete-orphan")
    knowledge_bases = relationship("KnowledgeBase", backref="session", cascade="all, delete-orphan")


class Message(Base):
    """Message to store messages exchanged in a session."""

    __tablename__ = "message"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(
        String(36), ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_type = Column(String(20), nullable=False)
    job_id = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=utc_now, nullable=False)
    others = Column(Text, nullable=True)


class KnowledgeBase(Base):
    """Knowledge Base to store knowledge base details"""

    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False)
    knowledge_type = Column(Text, nullable=False)
    session_id = Column(
        String(36), ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description = Column(Text)
    timestamp = Column(DateTime, default=utc_now, nullable=False)


class File(Base):
    """File to store file details."""

    __tablename__ = "file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False)
    path = Column(Text, nullable=False)

    file_to_kb = relationship("FileToKB", backref="file", cascade="all, delete-orphan")


class FileToKB(Base):
    """File to knowledge base association model."""

    __tablename__ = "file_to_kb"

    id = Column(String(36), ForeignKey("file.id", ondelete="CASCADE"), primary_key=True)
    name = Column(Text)
    kb_id = Column(String(36), ForeignKey("knowledge_base.id", ondelete="CASCADE"))
    chunk_ids = Column(Text)
    status = Column(String(36))
    config = Column(Text)
    timestamp = Column(DateTime, default=utc_now, nullable=False)


class GraphDB(Base):
    """GraphDB to store graph database details."""

    __tablename__ = "graph_db"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip = Column(Text, nullable=False)
    port = Column(Text, nullable=False)
    user = Column(Text, nullable=False)
    pwd = Column(Text, nullable=False)
    desc = Column(Text, nullable=False)
    name = Column(Text, nullable=False)
    is_default_db = Column(Boolean, nullable=False)
