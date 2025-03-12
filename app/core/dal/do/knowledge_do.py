from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.dal.database import Do


class KnowledgeBaseDo(Do):  # type: ignore
    """Knowledge Base to store knowledge base details"""

    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(36), nullable=False)
    knowledge_type = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False)  # FK constraint

    files = relationship("FileDo", secondary="kb_file_mapping", backref="knowledge_bases")


class KbFileMappingDo(Do):  # type: ignore
    """Knowledge Base to File association model."""

    __tablename__ = "kb_file_mapping"

    kb_id = Column(
        String(36), ForeignKey("knowledge_base.id", ondelete="CASCADE"), primary_key=True
    )
    file_id = Column(String(36), ForeignKey("file.id", ondelete="CASCADE"), primary_key=True)
