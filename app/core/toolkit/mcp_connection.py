from contextlib import AsyncExitStack
import threading
from typing import Any, List, Optional, cast
from urllib.parse import urljoin

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.websocket import websocket_client
from mcp.types import Tool as McpBaseTool

from app.core.common.type import McpTransportType
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig
from app.core.toolkit.tool_connection import ToolConnection


class McpConnection(ToolConnection):
    """Concrete implementation for interacting with MCP (Model Context Protocol) services.

    Manages connections to MCP servers through various transport protocols including
    STDIO, SSE, WebSocket, and Streamable HTTP.
    """

    def __init__(self, tool_group_config: McpConfig):
        super().__init__()
        self._mcp_config: McpConfig = tool_group_config
        self._session: Optional[ClientSession] = None
        self._cached_tools: List[McpBaseTool] = []
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._lock = threading.Lock()

    @property
    def transport_config(self) -> McpTransportConfig:
        """Get the transport configuration from the MCP service."""
        return self._mcp_config.transport_config

    async def call(self, tool_name: str, **kwargs) -> Any:
        """Execute a tool call through this connection.

        Args:
            tool_name: Name of the tool to call.
            **kwargs: Arguments to pass to the tool.

        Returns:
            The result content from the tool execution.
        """
        with self._lock:
            if self._session is None:
                raise RuntimeError("MCP connection is not initialized.")

            result = await self._session.call_tool(tool_name, kwargs or {})
            return result.content

    async def close(self) -> None:
        """Close and release MCP connection resources.

        Safely closes the session and cleans up transport resources.
        """
        with self._lock:
            if self._session is None:
                return

            # Close session and transport resources
            await self._exit_stack.aclose()

            self._session = None

    async def connect(self) -> None:
        """Establish MCP connection based on transport type.

        Creates the appropriate transport connection (STDIO, SSE, WebSocket, or
        Streamable HTTP) and initializes the session.
        """
        with self._lock:
            if self._session is not None:
                return

            transport_config = self.transport_config

            # Establish transport connection
            if transport_config.transport_type == McpTransportType.STDIO:
                await self._connect_stdio()
            elif transport_config.transport_type == McpTransportType.SSE:
                await self._connect_sse()
            elif transport_config.transport_type == McpTransportType.WEBSOCKET:
                await self._connect_websocket()
            elif transport_config.transport_type == McpTransportType.STREAMABLE_HTTP:
                await self._connect_streamable_http()
            else:
                raise ValueError(f"Unsupported transport type: {transport_config.transport_type}")

            if self._session is None:
                raise RuntimeError("MCP session was not properly connected.")

            # Initialize session
            session: ClientSession = cast(ClientSession, self._session)
            await session.initialize()

    async def _connect_stdio(self):
        """Initialize STDIO transport connection using AsyncExitStack."""
        config = self.transport_config
        server_params = StdioServerParameters(
            command=config.command, args=config.args or [], env=config.env
        )
        transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _connect_sse(self):
        """Initialize SSE transport connection using AsyncExitStack."""
        config = self.transport_config
        joined_url = urljoin(config.url, "sse")
        transport = await self._exit_stack.enter_async_context(
            sse_client(
                url=joined_url,
                headers=config.headers,
                timeout=config.timeout,
                sse_read_timeout=config.sse_read_timeout,
            )
        )
        read_stream, write_stream = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _connect_websocket(self):
        """Initialize WebSocket transport connection using AsyncExitStack."""
        config = self.transport_config
        base_url = config.url.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
        joined_url = urljoin(base_url, "ws")
        transport = await self._exit_stack.enter_async_context(websocket_client(joined_url))
        read_stream, write_stream = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _connect_streamable_http(self):
        """Initialize Streamable HTTP transport connection using AsyncExitStack."""
        config = self.transport_config
        joined_url = urljoin(config.url, "streamable")
        transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(joined_url, headers=config.headers)
        )
        read_stream, write_stream, _ = transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def list_tools(self) -> List[McpBaseTool]:
        """Get available tools from MCP server with caching support.

        Returns cached tools if available, otherwise fetches from the server.

        Returns:
            List of available MCP tools.
        """
        if self._cached_tools:
            return self._cached_tools
        if self._session is None:
            await self.connect()

        assert self._session is not None, "MCP session is not initialized"
        response = await self._session.list_tools()
        await self.close()
        self._cached_tools = response.tools
        return self._cached_tools
