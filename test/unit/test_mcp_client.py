from unittest.mock import AsyncMock, MagicMock, patch

from mcp.types import CallToolResult, TextContent, Tool as McpBaseTool
import pytest

from app.core.common.type import McpTransportType
from app.core.toolkit.mcp_service import McpService, McpTransportConfig
from test.resource.init_server import init_server

init_server()


@pytest.fixture
def stdio_config():
    """Fixture for STDIO transport configuration."""
    return McpTransportConfig(
        transport_type=McpTransportType.STDIO,
        command="npx",
        args=["@playwright/mcp@latest", "--port", "8931"],
    )


@pytest.fixture
def sse_config():
    """Fixture for SSE transport configuration."""
    return McpTransportConfig(
        transport_type=McpTransportType.SSE,
        url="http://localhost:8931",
        timeout=5.0,
        sse_read_timeout=300.0,
    )


@pytest.fixture
def websocket_config():
    """Fixture for WebSocket transport configuration."""
    return McpTransportConfig(
        transport_type=McpTransportType.WEBSOCKET,
        url="ws://localhost:8931",
    )


@pytest.fixture
def mock_session():
    """Fixture for mock MCP session."""
    session = AsyncMock()
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock()
    session.call_tool = AsyncMock()
    return session


@pytest.fixture
def mock_tools():
    """Fixture for mock MCP tools."""
    return [
        McpBaseTool(
            name="navigate_to",
            description="Navigate to a specific URL",
            inputSchema={
                "type": "object",
                "properties": {"url": {"type": "string", "description": "URL to navigate to"}},
                "required": ["url"],
            },
        ),
        McpBaseTool(
            name="get_page_content",
            description="Get the content of the current page",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@pytest.mark.asyncio
async def test_init(sse_config):
    """Test McpTool initialization."""
    tool = McpService(transport_config=sse_config)

    assert tool._transport_config == sse_config
    assert not tool._initialized
    assert not tool.is_connected
    assert len(tool._cached_tools) == 0


@pytest.mark.asyncio
async def test_connect_sse_success(sse_config, mock_session):
    """Test successful SSE connection."""
    tool = McpService(transport_config=sse_config)

    with (
        patch("app.core.toolkit.mcp_client.sse_client") as mock_sse_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        # mock the transport
        mock_transport = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_sse_client.return_value.__aexit__ = AsyncMock()

        # mock the session
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        connected_tool = await tool.connect()

        assert connected_tool is tool
        assert tool.is_connected
        mock_session.initialize.assert_called_once()


@pytest.mark.asyncio
async def test_connect_stdio_success(stdio_config, mock_session):
    """Test successful STDIO connection."""
    tool = McpService(transport_config=stdio_config)

    with (
        patch("app.core.toolkit.mcp_client.stdio_client") as mock_stdio_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        # mock the transport
        mock_transport = (AsyncMock(), AsyncMock())
        mock_stdio_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_stdio_client.return_value.__aexit__ = AsyncMock()

        # mock the session
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        connected_tool = await tool.connect()

        assert connected_tool is tool
        assert tool.is_connected


@pytest.mark.asyncio
async def test_connect_websocket_success(websocket_config, mock_session):
    """Test successful WebSocket connection."""
    tool = McpService(transport_config=websocket_config)

    with (
        patch("app.core.toolkit.mcp_client.websocket_client") as mock_ws_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        # mock the transport
        mock_transport = (AsyncMock(), AsyncMock())
        mock_ws_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_ws_client.return_value.__aexit__ = AsyncMock()

        # mock the session
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        connected_tool = await tool.connect()

        assert connected_tool is tool
        assert tool.is_connected


@pytest.mark.asyncio
async def test_connect_unsupported_transport():
    """Test connection with unsupported transport type."""
    # create config with invalid transport type
    config = McpTransportConfig(transport_type="INVALID")  # type: ignore
    tool = McpService(transport_config=config)

    with pytest.raises(ValueError, match="Unsupported transport type"):
        await tool.connect()


@pytest.mark.asyncio
async def test_connect_initialization_failure(sse_config):
    """Test connection failure during initialization."""
    tool = McpService(transport_config=sse_config)

    with patch("app.core.toolkit.mcp_client.sse_client") as mock_sse_client:
        mock_sse_client.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            await tool.connect()

        assert not tool.is_connected


@pytest.mark.asyncio
async def test_get_tools_with_cache(sse_config, mock_session, mock_tools):
    """Test get_tools with caching."""
    tool = McpService(transport_config=sse_config)

    # pre-populate cache
    tool._cached_tools = mock_tools

    result = await tool.list_tools()

    assert result == mock_tools
    # should not call session methods when cache is populated
    mock_session.list_tools.assert_not_called()


@pytest.mark.asyncio
async def test_get_tools_without_cache(sse_config, mock_session, mock_tools):
    """Test get_tools without cache."""
    tool = McpService(transport_config=sse_config)

    with (
        patch("app.core.toolkit.mcp_client.sse_client") as mock_sse_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        # mock successful connection
        mock_transport = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        # mock list_tools response
        mock_response = MagicMock()
        mock_response.tools = mock_tools
        mock_session.list_tools.return_value = mock_response

        result = await tool.list_tools()

        assert result == mock_tools
        assert tool._cached_tools == mock_tools
        mock_session.list_tools.assert_called_once()


@pytest.mark.asyncio
async def test_call_tool_success(sse_config, mock_session):
    """Test successful tool call."""
    tool = McpService(transport_config=sse_config)

    with (
        patch("app.core.toolkit.mcp_client.sse_client") as mock_sse_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        # mock successful connection
        mock_transport = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        # mock tool call response
        mock_content = [TextContent(type="text", text="Tool executed successfully")]
        mock_result = CallToolResult(content=mock_content)
        mock_session.call_tool.return_value = mock_result

        result = await tool.call_tool("navigate_to", param={"url": "https://example.com"})

        assert result == mock_content
        mock_session.call_tool.assert_called_once_with(
            "navigate_to", {"param": {"url": "https://example.com"}}
        )


@pytest.mark.asyncio
async def test_call_tool_without_params(sse_config, mock_session):
    """Test tool call without parameters."""
    tool = McpService(transport_config=sse_config)

    with (
        patch("app.core.toolkit.mcp_client.sse_client") as mock_sse_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        # mock successful connection
        mock_transport = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        # mock tool call response
        mock_content = [TextContent(type="text", text="Page content")]
        mock_result = CallToolResult(content=mock_content)
        mock_session.call_tool.return_value = mock_result

        result = await tool.call_tool("get_page_content")

        assert result == mock_content
        mock_session.call_tool.assert_called_once_with("get_page_content", {})


@pytest.mark.asyncio
async def test_url_joining_for_sse(mock_session):
    """Test URL joining for SSE transport."""
    config = McpTransportConfig(
        transport_type=McpTransportType.SSE,
        url="http://localhost:8931",  # without trailing slash
    )
    tool = McpService(transport_config=config)

    with (
        patch("app.core.toolkit.mcp_client.sse_client") as mock_sse_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        mock_transport = (AsyncMock(), AsyncMock())
        mock_sse_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_sse_client.return_value.__aexit__ = AsyncMock()
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        await tool.connect()

        # verify the URL was properly joined
        mock_sse_client.assert_called_once()
        call_args = mock_sse_client.call_args[1]
        assert call_args["url"] == "http://localhost:8931/sse"


@pytest.mark.asyncio
async def test_websocket_url_conversion(mock_session):
    """Test WebSocket URL scheme conversion."""
    config = McpTransportConfig(
        transport_type=McpTransportType.WEBSOCKET,
        url="http://localhost:8931",  # HTTP should be converted to WS
    )
    tool = McpService(transport_config=config)

    with (
        patch("app.core.toolkit.mcp_client.websocket_client") as mock_ws_client,
        patch("app.core.toolkit.mcp_client.ClientSession") as mock_client_session,
    ):
        mock_transport = (AsyncMock(), AsyncMock())
        mock_ws_client.return_value.__aenter__ = AsyncMock(return_value=mock_transport)
        mock_ws_client.return_value.__aexit__ = AsyncMock()
        mock_client_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_client_session.return_value.__aexit__ = AsyncMock()

        await tool.connect()

        # verify the URL scheme was converted
        mock_ws_client.assert_called_once()
        call_args = mock_ws_client.call_args[0]
        assert call_args[0] == "ws://localhost:8931/ws"
