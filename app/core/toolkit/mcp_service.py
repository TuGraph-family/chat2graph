import json
from typing import List

from git import Optional
from mcp.types import Tool as McpBaseTool

from app.core.model.task import ToolCallContext
from app.core.service.tool_connection_service import ToolConnectionService
from app.core.toolkit.mcp_tool import McpTool
from app.core.toolkit.tool import Tool
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

    async def create_connection(
        self, tool_call_ctx: Optional[ToolCallContext] = None
    ) -> ToolConnection:
        """Create a connection to the tool group."""
        tool_connection_service: ToolConnectionService = ToolConnectionService.instance
        return await tool_connection_service.get_or_create_connection(
            tool_group_id=self.get_id(),
            tool_group_config=self._tool_group_config,
            tool_call_ctx=tool_call_ctx,
        )

    async def list_tools(self) -> List[Tool]:
        """Get available tool list from MCP server, with caching support."""
        connection = await self.create_connection()
        mcp_base_tools: List[McpBaseTool] = await connection.list_tools()
        tools: List[Tool] = []
        for mcp_base_tool in mcp_base_tools:
            tool_description = mcp_base_tool.description + "\n" if mcp_base_tool.description else ""
            tools.append(
                McpTool(
                    name=mcp_base_tool.name,
                    description=(
                        tool_description
                        + "\tInput Schema:\n"
                        + json.dumps(mcp_base_tool.inputSchema, indent=4)
                    ),
                    tool_group=self,
                )
            )
        return tools
