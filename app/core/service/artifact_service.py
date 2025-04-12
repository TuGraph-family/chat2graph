from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from app.core.common.singleton import Singleton
from app.core.dal.dao.artifact_dao import ArtifactDao
from app.core.model.artifact import (
    Artifact,
    ContentType,
)


class ArtifactService(metaclass=Singleton):
    """Service for managing artifacts throughout their lifecycle.

    This service provides high-level operations for creating, retrieving,
    updating, and deleting artifacts.

    # TODO: support retract method
    """

    def __init__(self):
        self._artifact_dao: ArtifactDao = ArtifactDao.instance

    def save_artifact(self, artifact: Artifact) -> str:
        """Create a new artifact or update an existing one.

        Args:
            artifact: The artifact to create or update

        Returns:
            str: ID of the artifact
        """
        artifact_do = self._artifact_dao.save_artifact(artifact)
        return str(artifact_do.id)

    def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get an artifact by its ID.

        Args:
            artifact_id: ID of the artifact to retrieve

        Returns:
            Optional[Artifact]: The artifact if found, None otherwise
        """
        return self._artifact_dao.get_artifact(artifact_id)

    def get_artifacts_by_job_id_and_type(
        self, job_id: str, content_type: ContentType
    ) -> List[Artifact]:
        """Get all artifacts for a job.

        Args:
            job_id (str): The job ID to query for
            content_type (ContentType): The content type of the artifacts

        Returns:
            List[Artifact]: List of artifacts for the job
        """
        return self._artifact_dao.get_artifacts_by_job_id_and_type(
            job_id=job_id, content_type=content_type
        )

    def delete_artifact(self, artifact_id: str) -> None:
        """Delete an artifact.

        Args:
            artifact_id (str): ID of the artifact to delete
        """
        self._artifact_dao.delete_artifact(artifact_id)

    def delete_artifacts_by_job_id(self, job_id: str) -> None:
        """Delete all artifacts for a job.

        Args:
            job_id (str): The job ID to delete artifacts for
        """
        self._artifact_dao.delete_artifacts_by_job_id(job_id=job_id)

    def increment_and_save(self, artifact: Artifact, new_content: Any) -> Artifact:
        """Increment the update of an artifact content.

        Args:
            artifact (Artifact): The artifact to update
            new_content (Any): The content to append/merge with existing content

        Returns:
            Artifact: The updated artifact
        """
        if not new_content:
            return artifact

        # get current content (deserialized)
        current_content = artifact.content
        content_type = artifact.content_type

        # increment the content
        artifact.content = self._increment_content(
            content_type=content_type,
            current_content=current_content,
            new_content=new_content,
        )

        # save the updated artifact
        self._artifact_dao.save_artifact(artifact)

        return artifact

    def _increment_content(
        self, content_type: ContentType, current_content: Any, new_content: Any
    ) -> Any:
        """Calculates the result of incrementally updating content based on its type.

        This function is designed to be pure: it takes the current state and
        new data, and returns the calculated new state without modifying the
        original inputs directly (it returns copies or new objects where needed).

        Args:
            content_type: The type of the content being processed.
            current_content: The existing content (deserialized).
            new_content: The new content to accumulate/merge (deserialized).

        Returns:
            The combined/updated content (deserialized), or potentially the
            original or new content in case of errors or non-applicable increments.
        """
        if new_content is None:
            return current_content

        # apply incremental update based on content type
        if content_type == ContentType.TEXT:
            base = str(current_content) if current_content is not None else ""
            addition = str(new_content)
            result_text = base + addition
            return result_text

        if content_type == ContentType.JSON:
            if isinstance(current_content, dict) and isinstance(new_content, dict):
                # create a copy and update it to avoid modifying original dict
                # use deepcopy for nested structures
                # update simply (last write wins on conflict)
                result_dict = deepcopy(current_content)
                result_dict.update(new_content)
                return result_dict
            elif isinstance(current_content, list) and isinstance(new_content, list):
                # create a new extended list
                result_list = current_content + new_content
                return result_list
            elif current_content is None:
                # if starting from scratch, take the new content (assuming it's valid JSON)
                # return a copy if mutable to prevent external modification
                return (
                    deepcopy(new_content) if isinstance(new_content, dict | list) else new_content
                )
            else:
                # TODO: use logger warning
                print(
                    f"Warning: Cannot incrementally update JSON. Incompatible types: "
                    f"{type(current_content)} and {type(new_content)}. Replacing with new_content."
                )
                # fallback: replace with new content (return a copy if mutable)
                return (
                    deepcopy(new_content)
                    if isinstance(new_content, dict | list)
                    else current_content
                )

        if content_type == ContentType.CSV:
            # ensure both parts are treated as strings
            base = str(current_content).rstrip() if current_content is not None else ""
            addition = str(new_content).strip()

            if not addition:
                return base

            if not base:
                return addition

            # simple header check: if addition starts with the last line of base, skip that line
            try:
                base_lines = base.split("\n")
                addition_lines = addition.split("\n")
                if (
                    len(base_lines) > 0
                    and len(addition_lines) > 1
                    and base_lines[-1] == addition_lines[0]
                ):
                    addition = "\n".join(addition_lines[1:])
            except Exception as e:
                # TODO: use logger warning
                print(f"Warning: Could not perform header check for CSV: {e}")

            # combine with a newline
            result_csv = base + "\n" + addition
            return result_csv

        if content_type == ContentType.GRAPH:
            # ensure current_content is a dict for merging, handle if None
            if current_content is None:
                current_content = {
                    "vertices": [],
                    "edges": [],
                }

            if isinstance(current_content, dict) and isinstance(new_content, dict):
                # start with a deep copy of the current graph structure
                result_graph = deepcopy(current_content)

                # ensure base structure exists in the result
                if "vertices" not in result_graph:
                    result_graph["vertices"] = []
                if "edges" not in result_graph:
                    result_graph["edges"] = []

                # safely extract new vertices/edges
                input_vertices = new_content.get("vertices", [])
                input_edges = new_content.get("edges", [])

                if not isinstance(input_vertices, list) or not isinstance(input_edges, list):
                    # TODO: use logger warning
                    print(
                        "Warning: New graph content 'vertices' or 'edges' is not a list. "
                        "Cannot merge."
                    )
                    # return original content as merge is not possible
                    return current_content

                # merge Vertices (ID-based, last write wins for properties)
                # ensure current vertices are dicts with 'id' before adding to lookup
                existing_vertices: Dict[Any, Dict] = {
                    v["id"]: v
                    for v in result_graph.get("vertices", [])
                    if isinstance(v, dict) and "id" in v
                }
                vertices_added_or_updated = 0
                for vertex in input_vertices:
                    if isinstance(vertex, dict) and "id" in vertex:
                        vertex_id = vertex["id"]
                        existing_vertices[vertex_id] = vertex
                        vertices_added_or_updated += 1
                result_graph["vertices"] = list(existing_vertices.values())

                # merge Edges (Source-Target-Label based, last write wins for properties)
                # ensure current edges are dicts with required keys before adding to lookup
                # use string representation of keys for reliable hashing
                existing_edges: Dict[Tuple[str, str, str], Dict] = {
                    (str(e.get("source")), str(e.get("target")), str(e.get("label"))): e
                    for e in result_graph.get("edges", [])
                    if isinstance(e, dict) and all(k in e for k in ["source", "target", "label"])
                }
                edges_added_or_updated = 0
                for edge in input_edges:
                    if isinstance(edge, dict) and all(
                        k in edge for k in ["source", "target", "label"]
                    ):
                        edge_key: Tuple[str, str, str] = (
                            str(edge["source"]),
                            str(edge["target"]),
                            str(edge["label"]),
                        )
                        existing_edges[edge_key] = edge  # add or replace
                        edges_added_or_updated += 1
                result_graph["edges"] = list(existing_edges.values())
                return result_graph

            else:
                # TODO: use logger warning
                print(
                    f"Warning: Cannot incrementally update graph. Incompatible types: "
                    f"{type(current_content)} and {type(new_content)}. Replacing with new_content."
                )
                # fallback: Replace, return a copy if mutable
                return deepcopy(new_content) if isinstance(new_content, dict) else current_content

        raise ValueError(f"Unsupported content type: {content_type}")
