from uuid import uuid4

from sqlalchemy import JSON, BigInteger, Column, String, Text, func

from app.core.dal.database import Do
from app.core.model.artifact import ArtifactMetadata, ArtifactStatus, ContentType


class ArtifactDo(Do):  # type: ignore
    """Database object for artifacts produced by agents"""

    __tablename__ = "artifact"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    timestamp = Column(BigInteger, server_default=func.strftime("%s", "now"))

    # status of the artifact as a string (will be converted to/from ArtifactStatus enum)
    status = Column(String(36), nullable=False, default=ArtifactStatus.CREATED.value)

    # source reference fields
    job_id = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False)

    # content fields
    # content_type uses ContentType enum values (stored as strings)
    content_type = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)  # stored as JSON string or other serialized format

    # handle for resource location
    handle = Column(String(255), nullable=True)

    # metadata fields
    metadata_version = Column(BigInteger, nullable=False, default=1)
    metadata_description = Column(Text, nullable=True)
    metadata_dict = Column(JSON, nullable=True)

    def __init__(self, **kwargs):
        """Initialize ArtifactDo with proper type conversion"""
        # convert enum to string for storage
        if "status" in kwargs and isinstance(kwargs["status"], ArtifactStatus):
            kwargs["status"] = kwargs["status"].value

        # convert ContentType enum to string for storage
        if "content_type" in kwargs and isinstance(kwargs["content_type"], ContentType):
            kwargs["content_type"] = kwargs["content_type"].value

        # extract source_reference fields
        if "source_reference" in kwargs:
            source_ref = kwargs.pop("source_reference")
            kwargs["job_id"] = source_ref.job_id
            kwargs["session_id"] = source_ref.session_id

        # extract metadata fields
        if (
            "metadata" in kwargs
            and hasattr(kwargs["metadata"], "version")
            and hasattr(kwargs["metadata"], "description")
            and hasattr(kwargs["metadata"], "metadata_dict")
        ):
            metadata_obj: ArtifactMetadata = kwargs.pop("metadata")
            kwargs["metadata_version"] = metadata_obj.version
            kwargs["metadata_description"] = metadata_obj.description
            kwargs["metadata_dict"] = metadata_obj.metadata_dict

        super().__init__(**kwargs)
