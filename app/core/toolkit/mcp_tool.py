from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.websocket import websocket_client
from mcp.types import Tool as McpBaseTool

from app.core.common.type import McpTransportType
from app.core.toolkit.tool import ToolSet


@dataclass
class McpTransportConfig:
    """Configuration for MCP transport.

    Attributes:
        transport_type (McpTransportType): Specifies MCP transport (STDIO, SSE, etc.);
            determines other relevant params.
        url (str): MCP server base URL; required for SSE, WEBSOCKET, STREAMABLE_HTTP.
            Defaults to "http://localhost:8931".
        command (str): Command for STDIO transport (e.g., 'npx'); not used by other transports.
            Defaults to "npx".
        args (Optional[List[str]]): Arguments for STDIO command (e.g., ['@playwright/mcp@latest']);
            not used by others. Defaults to None.
        env (Dict[str, str]): Environment variables for STDIO command; not used by others.
            Defaults to an empty dict.
        headers (Dict[str, Any]): HTTP headers for requests; used by SSE, STREAMABLE_HTTP.
            Defaults to an empty dict.
        timeout (float): Connection timeout (seconds); primarily for SSE initial connection.
            Defaults to 5.0.
        sse_read_timeout (float): Read timeout (seconds) for SSE streaming (e.g., 60*5.0);
            specific to SSE. Defaults to 300.0.
    """
    transport_type: McpTransportType
    url: str = "http://localhost:8931"
    command: str = "npx"
    args: Optional[List[str]] = None
    env: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 5.0
    sse_read_timeout: float = 300.0

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "McpTransportConfig":
        """Create an instance from a dictionary."""
        transport_type = McpTransportType(config.get("transport_type", "stdio"))
        url = config.get("url", "http://localhost:8931")
        command = config.get("command", "npx")
        args = config.get("args", None)
        env = config.get("env", {})
        headers = config.get("headers", {})
        timeout = config.get("timeout", 5.0)
        sse_read_timeout = config.get("sse_read_timeout", 300.0)

        return cls(
            transport_type=transport_type,
            url=url,
            command=command,
            args=args,
            env=env,
            headers=headers,
            timeout=timeout,
            sse_read_timeout=sse_read_timeout,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "transport_type": self.transport_type.value,
            "url": self.url,
            "command": self.command,
            "args": self.args,
            "env": self.env,
            "headers": self.headers,
            "timeout": self.timeout,
            "sse_read_timeout": self.sse_read_timeout,
        }

class McpTool(ToolSet):
    """MCP client supports multiple transport methods, including Stdio, SSE, WebSocket,
    and Streamable HTTP. And ensure that the MCP server is started and running on the specified
    port when using.

    Attributes:
        _session (Optional[ClientSession]): MCP client session instance.
        _exit_stack (AsyncExitStack): Async context manager for automatic resource cleanup.
        _transport_config (McpTransportConfig): Transport configuration object.
        _initialized (bool): Flag indicating if the client has been initialized.
        _cached_tools (List[McpBaseTool]): List of cached tools from the MCP server.
    """

    def __init__(
        self,
        transport_config: McpTransportConfig,
        id: Optional[str] = None,
    ):
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()
        self._transport_config: McpTransportConfig = transport_config
        self._initialized: bool = False

        self._cached_tools: List[McpBaseTool] = []

        super().__init__(
            id=id or str(uuid4()),
            name=self.call_tool.__name__,
            description=self.call_tool.__doc__ or "",
            function=self.call_tool,
            list_functions=self.get_tools,
        )

    async def connect(self) -> "McpTool":
        """Actively connect to MCP server"""
        if self.is_connected:
            return self
        await self._initialize()
        return self

    async def disconnect(self) -> "McpTool":
        """Actively disconnect"""
        await self.aclose()
        return self

    async def _initialize(self):
        """Initialize connection based on transport type."""
        try:
            if self._transport_config.transport_type == McpTransportType.STDIO:
                await self._initialize_stdio()
            elif self._transport_config.transport_type == McpTransportType.SSE:
                await self._initialize_sse()
            elif self._transport_config.transport_type == McpTransportType.WEBSOCKET:
                await self._initialize_websocket()
            elif self._transport_config.transport_type == McpTransportType.STREAMABLE_HTTP:
                await self._initialize_streamable_http()
            else:
                raise ValueError(
                    f"Unsupported transport type: {self._transport_config.transport_type}"
                )

            if self._session is None:
                raise RuntimeError("MCP session was not properly initialized.")

            await self._session.initialize()
            self._initialized = True
        except Exception as e:
            await self._exit_stack.aclose()
            self._initialized = False
            raise e

    async def _initialize_stdio(self):
        """Initialize Stdio connection."""
        server_params = StdioServerParameters(
            command=self._transport_config.command,
            args=self._transport_config.args or ["@playwright/mcp@latest"],
            env=self._transport_config.env,
        )

        stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _initialize_sse(self):
        """Initialize SSE connection."""
        base_url = self._transport_config.url
        if not base_url.endswith('/'):
            base_url += '/'
        joined_url = urljoin(base_url, "sse")

        headers = self._transport_config.headers
        timeout = self._transport_config.timeout
        sse_read_timeout = self._transport_config.sse_read_timeout

        sse_transport = await self._exit_stack.enter_async_context(
            sse_client(
                url=joined_url,
                headers=headers,
                timeout=timeout,
                sse_read_timeout=sse_read_timeout,
            )
        )
        read_stream, write_stream = sse_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _initialize_websocket(self):
        """Initialize WebSocket connection."""
        base_url = self._transport_config.url

        # adjust scheme for WebSocket if necessary
        if base_url.startswith("http://"):
            base_url = base_url.replace("http://", "ws://", 1)
        elif base_url.startswith("https://"):
            base_url = base_url.replace("https://", "wss://", 1)

        if not base_url.endswith('/'):
            base_url += '/'
        joined_url = urljoin(base_url, "ws")

        ws_transport = await self._exit_stack.enter_async_context(
            websocket_client(joined_url)
        )
        read_stream, write_stream = ws_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def _initialize_streamable_http(self):
        """Initialize Streamable HTTP connection."""
        base_url = self._transport_config.url
        if not base_url.endswith('/'):
            base_url += '/'
        joined_url = urljoin(base_url, "streamable")
        headers = self._transport_config.headers

        http_transport = await self._exit_stack.enter_async_context(
            streamablehttp_client(joined_url, headers=headers)
        )
        read_stream, write_stream, _ = http_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

    async def aclose(self):
        """Close MCP session and transport connection."""
        if self._initialized:
            await self._exit_stack.aclose()
            self._initialized = False

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._initialized and self._session is not None

    async def get_tools(self) -> List[McpBaseTool]:
        """Dynamically get available tool list from MCP server, with caching support."""
        if len(self._cached_tools) > 0:
            return self._cached_tools

        await self.connect()
        assert self._session is not None

        response = await self._session.list_tools()
        tools = response.tools

        # cache tool list
        self._cached_tools = tools

        await self.disconnect()
        return tools

    async def call_tool(
        self, tool_name: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Call a tool through the established MCP session."""
        await self.connect()
        if self._session is None:
            raise RuntimeError("MCP session was not properly initialized.")

        result = await self._session.call_tool(tool_name, params or {})
        return result.content
