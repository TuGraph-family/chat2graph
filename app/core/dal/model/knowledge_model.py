import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.dal.database import Base


class KnowledgeBaseModel(Base):  # type: ignore
    """Knowledge Base to store knowledge base details"""

    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False)
    knowledge_type = Column(Text, nullable=False)
    session_id = Column(
        String(36), ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True
    )

    files = relationship("FileModel", secondary="kb_to_file", backref="knowledge_bases")


class FileModel(Base):  # type: ignore
    """File to store file details."""

    __tablename__ = "file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(
        String(36), ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(Text, nullable=False)
    path = Column(Text, nullable=False)


class KbToFileModel(Base):  # type: ignore
    """Knowledge Base to File association model."""

    __tablename__ = "kb_to_file"

    kb_id = Column(
        String(36), ForeignKey("knowledge_base.id", ondelete="CASCADE"), primary_key=True
    )
    file_id = Column(String(36), ForeignKey("file.id", ondelete="CASCADE"), primary_key=True)


class GraphDBModel(Base):  # type: ignore
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
