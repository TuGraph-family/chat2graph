from uuid import uuid4

from sqlalchemy import Column, String, Text, BigInteger, func

from app.core.dal.database import Do


class KnowledgeBaseDo(Do):  # type: ignore
    """Knowledge Base to store knowledge base details"""

    __tablename__ = "knowledge_base"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(36), nullable=False)
    knowledge_type = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False)  # FK constraint
    description = Column(Text)
    category = Column(String(36), nullable=False)
    timestamp = Column(BigInteger, server_default=func.strftime("%s", "now"))


class FileKbMappingDo(Do):  # type: ignore
    """File to knowledge base association model."""

    __tablename__ = "file_kb_mapping"

    id = Column(String(36), primary_key=True)  # FK constraint
    name = Column(Text)
    kb_id = Column(String(36))  # FK constraint
    chunk_ids = Column(Text)
    status = Column(String(36))
    config = Column(Text)
    type = Column(String(36), nullable=False)
    size = Column(String(36), nullable=False)
    timestamp = Column(BigInteger, server_default=func.strftime("%s", "now"))
