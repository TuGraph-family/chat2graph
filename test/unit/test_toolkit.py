from typing import List

import networkx as nx
import pytest

from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.toolkit import Toolkit
from test.resource.tool_resource import Query


@pytest.fixture
def operator_id():
    """Create a unique operator ID for testing."""
    return "test_operator_id"


@pytest.fixture
def sample_actions():
    """Create sample actions for testing."""
    return [
        Action(id=f"action {i}", name=f"Action {i}", description=f"Description {i}")
        for i in range(1, 5)
    ]


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""
    return [Query(id=f"tool {i}") for i in range(1, 5)]


@pytest.fixture
def toolkit_service():
    """Create a toolkit service for testing."""
    return ToolkitService.instance or ToolkitService()


@pytest.fixture
def populated_toolkit_service(
    operator_id: str,
    toolkit_service: ToolkitService,
    sample_actions: List[Action],
    sample_tools: List[Query],
):
    """Create a toolkit populated with sample data."""
    action1, action2, action3, action4 = sample_actions
    tool1, tool2, tool3, tool4 = sample_tools

    # add actions with connections
    toolkit_service.add_action(
        id=operator_id,
        action=action1,
        next_actions=[(action2, 0.8), (action3, 0.6)],
        prev_actions=[],
    )
    toolkit_service.add_action(
        id=operator_id,
        action=action2,
        next_actions=[(action3, 0.7), (action4, 0.9)],
        prev_actions=[(action1, 0.8)],
    )
    toolkit_service.add_action(
        id=operator_id,
        action=action3,
        next_actions=[(action4, 0.7)],
        prev_actions=[(action1, 0.6), (action2, 0.7)],
    )
    toolkit_service.add_action(
        id=operator_id,
        action=action4,
        next_actions=[],
        prev_actions=[(action2, 0.9), (action3, 0.7)],
    )

    # add tools with connections
    toolkit_service.add_tool(id=operator_id, tool=tool1, connected_actions=[(action1, 0.9)])
    toolkit_service.add_tool(id=operator_id, tool=tool2, connected_actions=[(action2, 0.8)])
    toolkit_service.add_tool(id=operator_id, tool=tool3, connected_actions=[(action3, 0.9)])
    toolkit_service.add_tool(id=operator_id, tool=tool4, connected_actions=[(action4, 0.8)])

    return toolkit_service


async def test_toolkit_initialization(operator_id: str, toolkit_service: ToolkitService):
    """Test toolkit initialization."""
    toolkit: Toolkit = toolkit_service.get_toolkit(id=operator_id)
    assert isinstance(toolkit.get_graph(), nx.DiGraph)
    assert len(toolkit.vertices()) == 0
    assert len(toolkit.edges()) == 0


def test_add_single_action(
    operator_id: str, toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test adding a single action without connections."""
    toolkit: Toolkit = toolkit_service.get_toolkit(id=operator_id)
    action = sample_actions[0]
    toolkit_service.add_action(id=operator_id, action=action, next_actions=[], prev_actions=[])

    assert len(toolkit.vertices()) == 1
    assert isinstance(toolkit.get_action(action.id), Action)
    assert toolkit.get_action(action.id) == action


def test_add_single_tool(
    operator_id: str,
    toolkit_service: ToolkitService,
    sample_actions: List[Action],
    sample_tools: List[Query],
):
    """Test adding a single tool with one action connection."""
    tool = sample_tools[0]
    action = sample_actions[0]
    toolkit_service.add_action(id=operator_id, action=action, next_actions=[], prev_actions=[])
    toolkit_service.add_tool(id=operator_id, tool=tool, connected_actions=[(action, 0.9)])
    toolkit: Toolkit = toolkit_service.get_toolkit(id=operator_id)

    assert len(toolkit.vertices()) == 2
    assert isinstance(toolkit.get_tool(tool.id), Query)
    assert toolkit.get_tool(tool.id) == tool


def test_graph_structure(operator_id: str, populated_toolkit_service: ToolkitService):
    """Test the overall graph structure."""
    graph = populated_toolkit_service.get_toolkit(id=operator_id)

    # verify vertex counts
    action_vertices = [n for n in graph.vertices() if graph.get_action(n)]
    tool_vertices = [n for n in graph.vertices() if graph.get_tool(n)]

    assert len(action_vertices) == 4
    assert len(tool_vertices) == 4

    # verify edge types and counts
    action_next_edges = [(u, v) for u, v in graph.edges() if graph.get_action(v)]
    tool_call_edges = [(u, v) for u, v in graph.edges() if graph.get_tool(v)]

    assert len(action_next_edges) == 5
    assert len(tool_call_edges) == 4

    # verify edge scores
    assert all(0 <= graph.get_score(u, v) <= 1 for u, v in graph.edges())


@pytest.mark.asyncio
async def test_recommend_subgraph_no_hops(
    operator_id: str, populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with no hops."""
    action1 = sample_actions[0]
    subgraph = await populated_toolkit_service.recommend_subgraph(
        id=operator_id, actions=[action1], threshold=0.5, hops=0
    )

    expected_vertices = {action1.id, "tool 1"}
    assert set(subgraph.vertices()) == expected_vertices
    assert len(subgraph.edges()) == 1


@pytest.mark.asyncio
async def test_recommend_subgraph_one_hop(
    operator_id: str, populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with one hop."""
    action1 = sample_actions[0]
    subgraph = await populated_toolkit_service.recommend_subgraph(
        id=operator_id, actions=[action1], threshold=0.5, hops=1
    )

    expected_vertices = {"action 1", "action 2", "action 3", "tool 1", "tool 2", "tool 3"}
    assert set(subgraph.vertices()) == expected_vertices
    assert len(subgraph.edges()) == 6


@pytest.mark.asyncio
async def test_recommend_subgraph_high_threshold(
    operator_id: str, populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with high threshold."""
    action1 = sample_actions[0]
    subgraph = await populated_toolkit_service.recommend_subgraph(
        id=operator_id, actions=[action1], threshold=0.8, hops=2
    )

    # only high-score edges should be included
    assert all(subgraph.get_score(u, v) >= 0.8 for u, v in subgraph.edges())


@pytest.mark.asyncio
async def test_recommend_subgraph_multiple_start_points(
    operator_id: str, populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with multiple starting actions."""
    action1, _, action3, _ = sample_actions
    subgraph = await populated_toolkit_service.recommend_subgraph(
        id=operator_id, actions=[action1, action3], threshold=0.6, hops=1
    )

    assert len(subgraph.vertices()) == 8  # all vertices should be included
    assert len(subgraph.edges()) == 9  # all edges above threshold
