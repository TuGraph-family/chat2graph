from uuid import uuid4

from sqlalchemy import Column, String, func, BigInteger

from app.core.dal.database import Do


class FileDescriptorDo(Do):  # type: ignore
    """File descriptor to store file details."""

    __tablename__ = "file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(36), nullable=False)
    path = Column(String(256), nullable=False)
    type = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False)  # FK constraint
    timestamp = Column(BigInteger, server_default=func.strftime("%s", "now"))
    size = Column(String(36), nullable=False)
