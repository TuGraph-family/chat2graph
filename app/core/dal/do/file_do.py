from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String

from app.core.dal.database import Do


class FileDo(Do):  # type: ignore
    """File to store file details."""

    __tablename__ = "file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    message_id = Column(
        String(36), ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(36), nullable=False)
    path = Column(String(256), nullable=False)
