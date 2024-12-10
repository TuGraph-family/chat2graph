from typing import List

import networkx as nx
import pytest

from app.toolkit.action.action import Action
from app.toolkit.tool.tool_resource import Query
from app.toolkit.toolkit import Toolkit, ToolkitGraphType


@pytest.fixture
def sample_actions():
    """Create sample actions for testing."""
    return [
        Action(id=f"action{i}", name=f"Action {i}", description=f"Description {i}")
        for i in range(1, 5)
    ]


@pytest.fixture
def sample_tools():
    """Create sample tools for testing."""
    return [Query(id=f"tool{i}") for i in range(1, 5)]


@pytest.fixture
def toolkit():
    """Create a clean toolkit instance."""
    return Toolkit()


@pytest.fixture
def populated_toolkit(
    toolkit: Toolkit, sample_actions: List[Action], sample_tools: List[Query]
):
    """Create a toolkit populated with sample data."""
    action1, action2, action3, action4 = sample_actions
    tool1, tool2, tool3, tool4 = sample_tools

    # add actions with connections
    toolkit.add_action(
        action=action1, next_actions=[(action2, 0.8), (action3, 0.6)], prev_actions=[]
    )
    toolkit.add_action(
        action=action2,
        next_actions=[(action3, 0.7), (action4, 0.9)],
        prev_actions=[(action1, 0.8)],
    )
    toolkit.add_action(
        action=action3,
        next_actions=[(action4, 0.7)],
        prev_actions=[(action1, 0.6), (action2, 0.7)],
    )
    toolkit.add_action(
        action=action4, next_actions=[], prev_actions=[(action2, 0.9), (action3, 0.7)]
    )

    # add tools with connections
    toolkit.add_tool(tool=tool1, connected_actions=[(action1, 0.9)])
    toolkit.add_tool(tool=tool2, connected_actions=[(action2, 0.8)])
    toolkit.add_tool(tool=tool3, connected_actions=[(action3, 0.9)])
    toolkit.add_tool(tool=tool4, connected_actions=[(action4, 0.8)])

    return toolkit


@pytest.mark.asyncio
async def test_toolkit_initialization(toolkit: Toolkit):
    """Test toolkit initialization."""
    assert isinstance(toolkit._toolkit_graph, nx.DiGraph)
    assert len(toolkit._toolkit_graph.nodes()) == 0
    assert len(toolkit._toolkit_graph.edges()) == 0


def test_add_single_action(toolkit, sample_actions):
    """Test adding a single action without connections."""
    action = sample_actions[0]
    toolkit.add_action(action=action, next_actions=[], prev_actions=[])

    assert len(toolkit._toolkit_graph.nodes()) == 1
    assert toolkit._toolkit_graph.nodes[action.id]["type"] == ToolkitGraphType.ACTION
    assert toolkit._toolkit_graph.nodes[action.id]["data"] == action


def test_add_single_tool(toolkit, sample_tools, sample_actions):
    """Test adding a single tool with one action connection."""
    tool = sample_tools[0]
    action = sample_actions[0]
    toolkit.add_action(action=action, next_actions=[], prev_actions=[])
    toolkit.add_tool(tool=tool, connected_actions=[(action, 0.9)])

    assert len(toolkit._toolkit_graph.nodes()) == 2
    assert toolkit._toolkit_graph.nodes[tool.id]["type"] == ToolkitGraphType.TOOL
    assert toolkit._toolkit_graph.nodes[tool.id]["data"] == tool


def test_graph_structure(populated_toolkit):
    """Test the overall graph structure."""
    graph = populated_toolkit._toolkit_graph

    # verify node counts
    action_nodes = [
        n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.ACTION
    ]
    tool_nodes = [
        n for n, d in graph.nodes(data=True) if d["type"] == ToolkitGraphType.TOOL
    ]

    assert len(action_nodes) == 4
    assert len(tool_nodes) == 4

    # verify edge types and counts
    action_next_edges = [
        (u, v, d)
        for u, v, d in graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_NEXT_ACTION
    ]
    tool_call_edges = [
        (u, v, d)
        for u, v, d in graph.edges(data=True)
        if d["type"] == ToolkitGraphType.ACTION_CALL_TOOL
    ]

    assert len(action_next_edges) == 5
    assert len(tool_call_edges) == 4

    # verify edge scores
    assert all(0 <= d["score"] <= 1 for _, _, d in graph.edges(data=True))


@pytest.mark.asyncio
async def test_recommend_subgraph_no_hops(
    populated_toolkit: Toolkit, sample_actions: List[Action]
):
    """Test subgraph recommendation with no hops."""
    action1 = sample_actions[0]
    subgraph = await populated_toolkit.recommend_tools(
        actions=[action1], threshold=0.5, hops=0
    )

    expected_nodes = {action1.id, "tool1"}
    assert set(subgraph.nodes()) == expected_nodes
    assert len(subgraph.edges()) == 1


@pytest.mark.asyncio
async def test_recommend_subgraph_one_hop(
    populated_toolkit: Toolkit, sample_actions: List[Action]
):
    """Test subgraph recommendation with one hop."""
    action1 = sample_actions[0]
    subgraph = await populated_toolkit.recommend_tools(
        actions=[action1], threshold=0.5, hops=1
    )

    expected_nodes = {"action1", "action2", "action3", "tool1", "tool2", "tool3"}
    assert set(subgraph.nodes()) == expected_nodes
    assert len(subgraph.edges()) == 6


@pytest.mark.asyncio
async def test_recommend_subgraph_high_threshold(
    populated_toolkit: Toolkit, sample_actions: List[Action]
):
    """Test subgraph recommendation with high threshold."""
    action1 = sample_actions[0]
    subgraph = await populated_toolkit.recommend_tools(
        actions=[action1], threshold=0.8, hops=2
    )

    # only high-score edges should be included
    assert all(d["score"] >= 0.8 for _, _, d in subgraph.edges(data=True))


@pytest.mark.asyncio
async def test_recommend_subgraph_multiple_start_points(
    populated_toolkit: Toolkit, sample_actions: List[Action]
):
    """Test subgraph recommendation with multiple starting actions."""
    action1, _, action3, _ = sample_actions
    subgraph = await populated_toolkit.recommend_tools(
        actions=[action1, action3], threshold=0.6, hops=1
    )

    assert len(subgraph.nodes()) == 8  # all nodes should be included
    assert len(subgraph.edges()) == 9  # all edges above threshold
