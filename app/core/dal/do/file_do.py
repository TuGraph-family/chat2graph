from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.dal.database import Do


class FileDo(Do):  # type: ignore
    """File to store file details."""

    __tablename__ = "file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(36), nullable=False)
    path = Column(String(256), nullable=False)

    file_kb_mapping = relationship("FileKbMappingDo", backref="file", cascade="all, delete-orphan")
