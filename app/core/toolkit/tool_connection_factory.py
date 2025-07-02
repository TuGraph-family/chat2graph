from app.core.toolkit.tool_config import McpConfig, ToolGroupConfig
from app.core.toolkit.tool_connection import ToolConnection


class ToolConnectionFactory:
    """Factory class for creating tool connections.

    This class provides methods to create connections to different types of tools
    based on the provided configuration.
    """

    @staticmethod
    async def create_connection(tool_group_config: ToolGroupConfig) -> ToolConnection:
        """Create a connection based on the tool group type."""
        if isinstance(tool_group_config, McpConfig):
            from app.core.toolkit.mcp_connection import McpConnection
            connection: McpConnection = McpConnection(tool_group_config=tool_group_config)
            await connection.connect()
            return connection
        else:
            raise ValueError("Unsupported tool group type for connection creation.")
