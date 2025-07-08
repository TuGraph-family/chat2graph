from typing import TYPE_CHECKING, Any, Callable, cast

from app.core.common.type import ToolType
from app.core.model.task import ToolCallContext
from app.core.toolkit.mcp_connection import McpConnection
from app.core.toolkit.tool import Tool

if TYPE_CHECKING:
    from app.core.toolkit.mcp_service import McpService


class McpTool(Tool):
    """MCP tool in the toolkit.

    Inherits from Tool and represents a tool that can be used with MCP.
    """

    def __init__(self, name: str, description: str, tool_group: "McpService"):
        """Initialize the MCP Tool with name, description, and MCP service."""
        super().__init__(
            name=name,
            description=description,
            function=self._create_function(name, description, tool_group),
            tool_type=ToolType.MCP_TOOL,
        )

        self._tool_group: McpService = tool_group

    def get_tool_group(self) -> "McpService":
        """Get the MCP service associated with this tool."""
        return self._tool_group

    def _create_function(
        self,
        name: str,
        description: str,
        tool_group: "McpService",
    ) -> Callable[..., Any]:
        """Create a placeholder function - actual execution is handled by ToolkitService."""

        async def function(tool_call_ctx: ToolCallContext, **kwargs) -> Any:
            connection: McpConnection = cast(
                McpConnection, await tool_group.create_connection(tool_call_ctx=tool_call_ctx)
            )
            result = await connection.call(tool_name=name, **kwargs)
            return result

        function.__name__ = name
        function.__doc__ = description
        return function

    def copy(self) -> "McpTool":
        """Create a copy of the MCP tool."""
        copied_tool = super().copy()
        return McpTool(
            name=copied_tool.name,
            description=copied_tool.description,
            tool_group=self._tool_group,
        )
