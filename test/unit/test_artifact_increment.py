from typing import Any, Dict

import pytest

from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.model.artifact import ContentType
from app.core.service.artifact_service import ArtifactService
from app.core.service.service_factory import ServiceFactory

DaoFactory.initialize(DbSession())
ServiceFactory.initialize()


@pytest.fixture
def artifact_service():
    """Fixture to provide an ArtifactService instance."""
    return ArtifactService.instance


@pytest.fixture
def initial_graph():
    """Fixture to provide a sample initial graph."""
    return {
        "vertices": [
            {
                "id": "1",
                "label": "A",
                "properties": {},
            },
            {
                "id": "2",
                "label": "B",
                "properties": {},
            },
        ],
        "edges": [
            {
                "source": "1",
                "target": "2",
                "label": "A_to_B",
                "properties": {},
            }
        ],
    }


@pytest.fixture
def new_graph():
    """Fixture to provide a sample graph update."""
    return {
        "vertices": [
            {
                "id": "2",
                "label": "B",
                "properties": {"updated": True},
            },  # updated vertex
            {
                "id": "3",
                "label": "C",
                "properties": {},
            },  # new vertex
        ],
        "edges": [
            {
                "source": "2",
                "target": "3",
                "label": "B_to_C",
                "properties": {},
            }
        ],
    }


def test_graph_merge(
    artifact_service: ArtifactService, initial_graph: Dict[str, Any], new_graph: Dict[str, Any]
):
    """Test merging two graph structures."""
    result = artifact_service._increment_content(
        content_type=ContentType.GRAPH, current_content=initial_graph, new_content=new_graph
    )

    # check that the result has the expected structure
    assert "vertices" in result
    assert "edges" in result

    # verify vertex count (2 original + 1 new = 3)
    assert len(result["vertices"]) == 3

    # verify edge count (1 original + 1 new = 2)
    assert len(result["edges"]) == 2

    # check that vertex 2 was updated with new properties
    vertex_2 = next((v for v in result["vertices"] if v["id"] == "2"), None)
    assert vertex_2 is not None
    assert "updated" in vertex_2["properties"]
    assert vertex_2["properties"]["updated"] is True

    # check that vertex 3 was added
    assert any(v["id"] == "3" for v in result["vertices"])

    # check that both edges exist
    edge_keys = [(e["source"], e["target"], e["label"]) for e in result["edges"]]
    assert ("1", "2", "A_to_B") in edge_keys
    assert ("2", "3", "B_to_C") in edge_keys


def test_graph_none_current_content(
    artifact_service: ArtifactService, initial_graph: Dict[str, Any]
):
    """Test graph increment when the current content is None."""
    result = artifact_service._increment_content(
        content_type=ContentType.GRAPH, current_content=None, new_content=initial_graph
    )

    # check that the result matches the initial graph structure
    assert len(result["vertices"]) == len(initial_graph["vertices"])
    assert len(result["edges"]) == len(initial_graph["edges"])

    # verify vertices were copied correctly
    vertex_ids = [v["id"] for v in result["vertices"]]
    assert "1" in vertex_ids
    assert "2" in vertex_ids

    # verify edge was copied correctly
    assert result["edges"][0]["source"] == "1"
    assert result["edges"][0]["target"] == "2"
    assert result["edges"][0]["label"] == "A_to_B"


def test_graph_none_new_content(artifact_service: ArtifactService, initial_graph: Dict[str, Any]):
    """Test that None new content returns current content unchanged."""
    result = artifact_service._increment_content(
        content_type=ContentType.GRAPH, current_content=initial_graph, new_content=None
    )

    # should return the original graph unchanged
    assert result == initial_graph


def test_graph_invalid_inputs(artifact_service: ArtifactService):
    """Test handling of invalid graph inputs."""
    # test with non-dict current_content
    result = artifact_service._increment_content(
        content_type=ContentType.GRAPH,
        current_content="not a dict",
        new_content={"vertices": [], "edges": []},
    )

    # should fallback to returning the new content
    assert isinstance(result, dict)
    assert "vertices" in result
    assert "edges" in result

    # test with non-dict new_content
    initial = {"vertices": [], "edges": []}
    result = artifact_service._increment_content(
        content_type=ContentType.GRAPH, current_content=initial, new_content="not a dict"
    )

    # should return the current content unchanged
    assert result == initial
