from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.common.type import McpTransportType, ToolGroupType


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
        transport_type = McpTransportType(config.get("transport_type", "STDIO"))
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


@dataclass
class ToolGroupConfig:
    """Configuration for a tool group.

    Attributes:
        id: Unique identifier for the tool group.
        type: Type of the tool group (MCP, PACKAGE, etc.).
        name: Name of the tool group.
    """

    type: ToolGroupType
    name: str


@dataclass
class McpConfig(ToolGroupConfig):
    """Configuration for MCP service.

    Attributes:
        ...
        transport_config (McpTransportConfig): Configuration for the MCP transport.
    """

    transport_config: McpTransportConfig
