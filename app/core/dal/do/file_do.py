from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, Text

from app.core.dal.database import Do


class FileDo(Do):  # type: ignore
    """File to store file details."""

    __tablename__ = "file"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    message_id = Column(
        String(36), ForeignKey("message.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(Text, nullable=False)
    path = Column(Text, nullable=False)
