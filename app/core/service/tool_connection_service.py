from typing import Dict

from git import Optional

from app.core.common.singleton import Singleton
from app.core.toolkit.tool_connection import ToolConnection
from app.core.toolkit.tool_connection_factory import ToolConnectionFactory
from app.core.toolkit.tool_group import ToolGroupConfig


class ToolConnectionService(metaclass=Singleton):
    """Service for managing MCP tool connections.

    Attributes:
        _connections (Dict[str, Dict[str, ToolConnection]]): A dictionary mapping operator IDs
            to their respective tool group connections. The structure is:
            {operator_id: {tool_group_id: tool_connection}}.
    """

    def __init__(self):
        # structure: {operator_id: {tool_group_id: tool_connection}}
        self._connections: Dict[str, Dict[str, ToolConnection]] = {}

    async def get_or_create_connection(
        self,
        tool_group_id: str,
        tool_group_config: ToolGroupConfig,
        operator_id: Optional[str] = None,
    ) -> ToolConnection:
        """Get or create a connection for the specified tool group.

        If an operator_id is provided, the connection will be associated with that operator.
        If no operator_id is provided, a new connection can be used temporarily, which will be
        closed after use.
        """
        if operator_id is None:
            return await ToolConnectionFactory.create_connection(
                tool_group_config=tool_group_config
            )

        if operator_id not in self._connections:
            self._connections[operator_id] = {}

        if tool_group_id not in self._connections[operator_id]:
            connection = await ToolConnectionFactory.create_connection(
                tool_group_config=tool_group_config
            )
            self._connections[operator_id][tool_group_id] = connection
        else:
            connection = self._connections[operator_id][tool_group_id]
        return connection

    async def destroy_connection(self, operator_id: str) -> None:
        """Destroy the specified connection."""
        if operator_id in self._connections:
            for connection in self._connections[operator_id].values():
                await connection.close()
            del self._connections[operator_id]
