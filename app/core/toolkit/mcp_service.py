from typing import List, cast

from git import Optional
from mcp.types import Tool as McpBaseTool

from app.core.service.tool_connection_service import ToolConnectionService
from app.core.toolkit.tool_config import McpConfig
from app.core.toolkit.tool_connection import ToolConnection
from app.core.toolkit.tool_group import ToolGroup


class McpService(ToolGroup):
    """MCP service supports multiple transport methods, including Stdio, SSE, WebSocket,
    and Streamable HTTP. And ensure that the MCP server is started and running on the specified
    port when using.

    Attributes:
        ...
    """

    def __init__(self, mcp_config: McpConfig):
        super().__init__(tool_group_config=mcp_config)

    async def create_connection(self, operator_id: Optional[str] = None) -> ToolConnection:
        """Create a connection to the tool group."""
        tool_connection_service: ToolConnectionService = ToolConnectionService.instance
        return await tool_connection_service.get_or_create_connection(
            tool_group_id=self.get_id(),
            tool_group_config=self._tool_group_config,
            operator_id=operator_id
        )

    async def list_tools(self) -> List[McpBaseTool]:
        """Get available tool list from MCP server, with caching support."""
        connection = await self.create_connection()
        return cast(List[McpBaseTool], await connection.list_tools())
