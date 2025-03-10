from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.dal.database import Base


class KnowledgeBaseDo(Base):  # type: ignore
    """Knowledge Base to store knowledge base details"""

    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(Text, nullable=False)
    knowledge_type = Column(Text, nullable=False)
    session_id = Column(String(36), nullable=False)  # FK constraint

    files = relationship("FileDo", secondary="kb_to_file", backref="knowledge_bases")


class KbToFileDo(Base):  # type: ignore
    """Knowledge Base to File association model."""

    __tablename__ = "kb_to_file"

    kb_id = Column(
        String(36), ForeignKey("knowledge_base.id", ondelete="CASCADE"), primary_key=True
    )
    file_id = Column(String(36), ForeignKey("file.id", ondelete="CASCADE"), primary_key=True)
