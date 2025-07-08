from typing import List

from mcp.types import Tool as McpBaseTool
import networkx as nx
import pytest

from app.core.common.type import McpTransportType, ToolGroupType
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.mcp_service import McpService
from app.core.toolkit.mcp_tool import McpTool
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig
from app.core.toolkit.toolkit import Toolkit
from test.resource.init_server import init_server
from test.resource.tool_resource import ExampleQuery

init_server()


def create_mock_mcp_tool(name: str, description: str) -> McpBaseTool:
    """Helper function to create a mock McpBaseTool for testing."""
    return McpBaseTool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "A search query"}},
            "required": ["query"],
        },
    )


class MockMcpService(McpService):
    """Mock McpService to simulate a tool group with a predefined list of tools."""

    def __init__(self, name: str, mock_tools: List[McpBaseTool]):
        config = McpConfig(
            type=ToolGroupType.MCP,
            name=name,
            transport_config=McpTransportConfig(
                transport_type=McpTransportType.STDIO,
            ),
        )
        super().__init__(mcp_config=config)
        self._mock_tools = mock_tools
        # override the auto-generated id for predictable testing
        self._id = f"group_{name}"

    async def list_tools(self) -> List[Tool]:
        """Return the mock list of tools."""
        return [
            McpTool(name=t.name, description=t.description, tool_group=self)
            for t in self._mock_tools
        ]


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
    _sample_tools: List[ExampleQuery] = []
    for i in range(1, 5):
        tool = ExampleQuery()
        tool._id = f"tool {i}"
        _sample_tools.append(tool)
    return _sample_tools


@pytest.fixture
def toolkit_service():
    """Create a clean toolkit service for each test."""
    toolkit_service = ToolkitService.instance or ToolkitService()
    toolkit_service._toolkit = Toolkit()
    return toolkit_service


@pytest.fixture
def populated_toolkit_service(
    toolkit_service: ToolkitService, sample_actions: List[Action], sample_tools: List[ExampleQuery]
):
    """Create a toolkit populated with sample actions and tools."""
    action1, action2, action3, action4 = sample_actions
    tool1, tool2, tool3, tool4 = sample_tools

    # add actions with connections
    toolkit_service.add_action(
        action=action1,
        next_actions=[(action2, 0.8), (action3, 0.6)],
        prev_actions=[],
    )
    toolkit_service.add_action(
        action=action2,
        next_actions=[(action3, 0.7), (action4, 0.9)],
        prev_actions=[(action1, 0.8)],
    )
    toolkit_service.add_action(
        action=action3,
        next_actions=[(action4, 0.7)],
        prev_actions=[(action1, 0.6), (action2, 0.7)],
    )
    toolkit_service.add_action(
        action=action4, next_actions=[], prev_actions=[(action2, 0.9), (action3, 0.7)]
    )

    # add tools with connections
    toolkit_service.add_tool(tool=tool1, connected_actions=[(action1, 0.9)])
    toolkit_service.add_tool(tool=tool2, connected_actions=[(action2, 0.8)])
    toolkit_service.add_tool(tool=tool3, connected_actions=[(action3, 0.9)])
    toolkit_service.add_tool(tool=tool4, connected_actions=[(action4, 0.8)])

    return toolkit_service


@pytest.fixture
def mock_mcp_service():
    """Fixture to create a mock MCP service with two tools."""
    mock_tools = [
        create_mock_mcp_tool("Search API", "Performs a search."),
        create_mock_mcp_tool("Calculator API", "Calculates a value."),
    ]
    return MockMcpService(name="api_service", mock_tools=mock_tools)


async def test_toolkit_initialization(populated_toolkit_service: ToolkitService):
    """Test toolkit initialization."""
    toolkit: Toolkit = populated_toolkit_service.get_toolkit()
    assert isinstance(toolkit.get_graph(), nx.DiGraph)
    assert len(toolkit.vertices()) == 8
    assert len(toolkit.edges()) == 5 + 4  # 5 action edges + 4 tool edges


def test_add_single_action(populated_toolkit_service: ToolkitService, sample_actions: List[Action]):
    """Test adding a single action without connections."""
    toolkit: Toolkit = populated_toolkit_service.get_toolkit()
    action = sample_actions[0]
    # re-adding an existing action
    populated_toolkit_service.add_action(action=action, next_actions=[], prev_actions=[])

    assert len(toolkit.vertices()) == 8  # no new vertex should be added
    assert isinstance(toolkit.get_action(action.id), Action)
    assert toolkit.get_action(action.id) == action


def test_add_single_tool(
    populated_toolkit_service: ToolkitService,
    sample_actions: List[Action],
    sample_tools: List[ExampleQuery],
):
    """Test adding a single tool with one action connection."""
    tool = sample_tools[0]
    action = sample_actions[0]
    populated_toolkit_service.add_action(action=action, next_actions=[], prev_actions=[])
    populated_toolkit_service.add_tool(tool=tool, connected_actions=[(action, 0.9)])
    toolkit: Toolkit = populated_toolkit_service.get_toolkit()

    assert len(toolkit.vertices()) == 8  # no new vertex, tool already exists
    assert isinstance(toolkit.get_tool(tool.id), ExampleQuery)
    assert toolkit.get_tool(tool.id).id != tool.id


def test_graph_structure(populated_toolkit_service: ToolkitService):
    """Test the overall graph structure."""
    graph = populated_toolkit_service.get_toolkit()

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
async def test_add_tool_group(
    populated_toolkit_service: ToolkitService,
    mock_mcp_service: MockMcpService,
    sample_actions: List[Action],
):
    """Test adding a tool group and its associated tools to the toolkit."""
    service = populated_toolkit_service
    action1 = sample_actions[0]

    # add the tool group, connecting its tools to action1
    service.add_tool_group(tool_group=mock_mcp_service, connected_actions=[(action1, 0.95)])

    toolkit = service.get_toolkit()
    mock_mcp_base_tool_names = {
        mcp_base_tool.name for mcp_base_tool in await mock_mcp_service.list_tools()
    }
    num_mock_mcp_base_tools = len(mock_mcp_base_tool_names)

    # 8 original vertices + 1 tool_group + 2 tools from the group
    assert len(toolkit.vertices()) == 8 + 1 + num_mock_mcp_base_tools
    # 9 original edges + 2 (action->tool) + 2 (group->tool)
    assert len(toolkit.edges()) == 9 + num_mock_mcp_base_tools + num_mock_mcp_base_tools

    # check that the tool group vertex exists
    group_id = mock_mcp_service.get_id()
    assert toolkit.get_tool_group(group_id) is not None

    # tools should be added to the toolkit
    tools: List[Tool] = []
    for tool_id in toolkit.successors(mock_mcp_service.get_id()):
        tool = toolkit.get_tool(tool_id)
        if tool is not None:
            tools.append(tool)
    assert len(tools) == num_mock_mcp_base_tools
    for tool in tools:
        assert tool.name in mock_mcp_base_tool_names


@pytest.mark.asyncio
async def test_add_tool_group_update_cleans_old_tools(
    toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test that re-adding a tool group cleans up old tools and adds new ones."""
    action1 = sample_actions[0]
    toolkit_service.add_action(action1, [], [])
    toolkit = toolkit_service.get_toolkit()

    # initial set of tools
    initial_tools = [create_mock_mcp_tool("Old API", "An old API.")]
    service1 = MockMcpService(name="api_service", mock_tools=initial_tools)
    toolkit_service.add_tool_group(service1, connected_actions=[(action1, 0.9)])

    # find the old tool's ID dynamically
    group_id = service1.get_id()
    old_tool_id = next(iter(toolkit.successors(group_id)))
    assert toolkit.get_tool(old_tool_id) is not None

    # new set of tools for the same service (same ID)
    updated_tools = [create_mock_mcp_tool("New API", "A new API.")]
    service2 = MockMcpService(name="api_service", mock_tools=updated_tools)
    assert group_id == service2.get_id()  # ensure IDs match

    toolkit_service.add_tool_group(service2, connected_actions=[(action1, 0.9)])

    # verify old tool is gone and new tool is present
    assert toolkit.get_tool(old_tool_id) is None
    new_tool_id = next(iter(toolkit.successors(group_id)))
    new_tool = toolkit.get_tool(new_tool_id)
    assert new_tool is not None
    assert new_tool.name == "New API"


@pytest.mark.asyncio
async def test_remove_group_cascades_to_tools(
    toolkit_service: ToolkitService,
    mock_mcp_service: MockMcpService,
    sample_actions: List[Action],
):
    """Test that removing a tool group also removes all its associated tools."""
    service = toolkit_service
    action1 = sample_actions[0]
    service.add_action(action1, [], [])
    service.add_tool_group(mock_mcp_service, connected_actions=[(action1, 0.9)])

    toolkit = service.get_toolkit()
    group_id = mock_mcp_service.get_id()
    tool_ids_before = [tool.id for tool in toolkit._tools.values()]

    assert len(tool_ids_before) == 2
    assert toolkit.get_tool_group(group_id) is not None

    # remove the group
    service.get_toolkit().remove_vertex(group_id)

    assert toolkit.get_tool_group(group_id) is None
    for tool_id in tool_ids_before:
        assert toolkit.get_tool(tool_id) is None
    assert len(toolkit._tools) == 0


@pytest.mark.asyncio
async def test_remove_tool_cascades_to_group(
    toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test removing the last tool of a group also removes the group itself."""
    service = toolkit_service
    action1 = sample_actions[0]
    service.add_action(action1, [], [])
    toolkit = service.get_toolkit()

    # create a group with a single tool
    single_tool_service = MockMcpService(
        "single_tool_service", [create_mock_mcp_tool("Solo", "A lone tool.")]
    )
    service.add_tool_group(single_tool_service, connected_actions=[(action1, 0.9)])

    group_id = single_tool_service.get_id()

    # find the tool ID dynamically as the sole successor of the group.
    successors = list(toolkit.successors(group_id))
    assert len(successors) == 1, "The group should have exactly one tool."
    tool_id = successors[0]

    assert toolkit.get_tool_group(group_id) is not None
    assert toolkit.get_tool(tool_id) is not None

    # remove the only tool using the public service method
    service.remove_tool(tool_id)

    # both the tool and its parent group (which is now empty) should be gone
    assert toolkit.get_tool(tool_id) is None
    assert toolkit.get_tool_group(group_id) is None


@pytest.mark.asyncio
async def test_recommend_subgraph_no_hops(
    populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with no hops."""
    action1 = sample_actions[0]
    subgraph = populated_toolkit_service.recommend_subgraph(
        actions=[action1], threshold=0.5, hops=0
    )

    expected_vertices = {action1.id, "tool 1"}
    assert set(subgraph.vertices()) == expected_vertices
    assert len(subgraph.edges()) == 1


@pytest.mark.asyncio
async def test_recommend_subgraph_one_hop(
    populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with one hop."""
    action1 = sample_actions[0]
    subgraph = populated_toolkit_service.recommend_subgraph(
        actions=[action1], threshold=0.5, hops=1
    )

    expected_vertices = {"action 1", "action 2", "action 3", "tool 1", "tool 2", "tool 3"}
    assert set(subgraph.vertices()) == expected_vertices
    assert len(subgraph.edges()) == 6


@pytest.mark.asyncio
async def test_recommend_subgraph_high_threshold(
    populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with high threshold."""
    action1 = sample_actions[0]
    subgraph = populated_toolkit_service.recommend_subgraph(
        actions=[action1], threshold=0.8, hops=2
    )

    # only high-score edges should be included
    assert all(subgraph.get_score(u, v) >= 0.8 for u, v in subgraph.edges())


@pytest.mark.asyncio
async def test_recommend_subgraph_multiple_start_points(
    populated_toolkit_service: ToolkitService, sample_actions: List[Action]
):
    """Test subgraph recommendation with multiple starting actions."""
    action1, _, action3, _ = sample_actions
    subgraph = populated_toolkit_service.recommend_subgraph(
        actions=[action1, action3], threshold=0.6, hops=1
    )

    assert len(subgraph.vertices()) == 8  # all vertices should be included
    assert len(subgraph.edges()) == 9  # all edges above threshold
