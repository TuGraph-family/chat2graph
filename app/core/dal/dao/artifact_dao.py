from typing import List

from sqlalchemy.orm import Session as SqlAlchemySession

from app.core.dal.dao.dao import Dao
from app.core.dal.do.artifact_do import ArtifactDo
from app.core.model.artifact import (
    Artifact,
    ArtifactMetadata,
    ArtifactStatus,
    ContentType,
    SourceReference,
)


class ArtifactDao(Dao[ArtifactDo]):
    """Data access object for artifacts."""

    def __init__(self, session: SqlAlchemySession):
        super().__init__(ArtifactDo, session)

    def save_artifact(self, artifact: Artifact) -> ArtifactDo:
        """Save an artifact to the database. If the artifact already exists, it will be updated."""
        artifact_do = self.parse_into_artifact_do(artifact)
        artifact_dict = {
            c.name: getattr(artifact_do, c.name) for c in artifact_do.__table__.columns
        }

        try:
            self.create(**artifact_dict)
        except Exception:
            # if creation fails (likely due to duplicate ID), update instead, and increment version
            artifact_dict.pop("id", None)
            artifact_dict["metadata_version"] = artifact.metadata.version + 1
            self.update(id=str(artifact_do.id), **artifact_dict)

        return artifact_do

    def get_artifact(self, id: str) -> Artifact:
        """Get an artifact by ID.

        Args:
            id (str): The ID of the artifact to retrieve

        Returns:
            Artifact: The retrieved artifact domain object

        Raises:
            ValueError: If no artifact with the given ID exists
        """
        artifact_do = self.get_by_id(id=id)
        if not artifact_do:
            raise ValueError(f"Artifact with ID {id} not found")
        return self.parse_into_artifact(artifact_do=artifact_do)

    def get_artifacts_by_job_id_and_type(
        self, job_id: str, content_type: ContentType
    ) -> List[Artifact]:
        """Get all artifacts for a given job ID.

        Args:
            job_id (str): The job ID to query for
            content_type (ContentType): The content type of the artifacts

        Returns:
            List[Artifact]: List of artifacts for the job
        """
        artifact_dos = (
            self.session.query(self._model)
            .filter(
                self._model.job_id == job_id,
                self._model.content_type == content_type.value,
            )
            .all()
        )
        return [self.parse_into_artifact(artifact_do) for artifact_do in artifact_dos]

    def delete_artifact(self, id: str) -> None:
        """Delete an artifact by ID."""
        return self.delete(id)

    def delete_artifacts_by_job_id(self, job_id: str) -> None:
        """Delete all artifacts for a given job ID."""
        artifact_dos = self.session.query(self._model).filter(self._model.job_id == job_id)
        for artifact_do in artifact_dos:
            self.delete(str(artifact_do.id))

    def parse_into_artifact_do(self, artifact: Artifact) -> ArtifactDo:
        """Convert a domain artifact object to a database object."""
        return ArtifactDo(
            id=artifact.id,
            timestamp=artifact.timestamp,
            status=artifact.status.value if artifact.status else ArtifactStatus.CREATED.value,
            job_id=artifact.source_reference.job_id,
            session_id=artifact.source_reference.session_id,
            content_type=artifact.content_type.value,
            content=artifact.serialize_content(),
            handle=artifact.handle,
            metadata=artifact.metadata,
        )

    def parse_into_artifact(self, artifact_do: ArtifactDo) -> Artifact:
        """Convert a database artifact object to a domain object.

        Args:
            artifact_do (ArtifactDo): The database artifact to convert

        Returns:
            Artifact: The domain artifact object
        """
        # parse content type - now always a ContentType enum
        content_type_value = str(artifact_do.content_type)
        try:
            content_type = ContentType(content_type_value)
        except ValueError as e:
            # fallback to binary if content type is not recognized
            raise ValueError(f"Invalid content type: {content_type_value}") from e

        return Artifact(
            id=str(artifact_do.id),
            timestamp=str(artifact_do.timestamp),
            status=ArtifactStatus(artifact_do.status),
            source_reference=SourceReference(
                job_id=str(artifact_do.job_id),
                session_id=str(artifact_do.session_id),
            ),
            content_type=content_type,
            content=Artifact.deserialize_content(
                content_type=content_type,
                content_str=str(artifact_do.content),
            ),
            handle=str(artifact_do.handle) if artifact_do.handle is not None else None,
            metadata=ArtifactMetadata(
                version=int(artifact_do.metadata_version),
                description=str(artifact_do.metadata_description)
                if artifact_do.metadata_description
                else "",
                metadata_dict=dict(artifact_do.metadata_dict) if artifact_do.metadata_dict else {},
            ),
        )
