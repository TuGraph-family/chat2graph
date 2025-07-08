from typing import Dict

from git import Optional

from app.core.common.singleton import Singleton
from app.core.model.task import ToolCallContext
from app.core.toolkit.tool_connection import ToolConnection
from app.core.toolkit.tool_connection_factory import ToolConnectionFactory
from app.core.toolkit.tool_group import ToolGroupConfig


class ToolConnectionService(metaclass=Singleton):
    """Service for managing MCP tool connections.

    Attributes:
        _connections (Dict[str, Dict[str, Dict[str, ToolConnection]]]): A dictionary mapping job IDs
            to operator IDs to their respective tool group connections. The structure is:
            {job_id: {operator_id: {tool_group_id: tool_connection}}}.
    """

    def __init__(self):
        # structure: {job_id: {operator_id: {tool_group_id: tool_connection}}}
        self._connections: Dict[str, Dict[str, Dict[str, ToolConnection]]] = {}

    async def get_or_create_connection(
        self,
        tool_group_id: str,
        tool_group_config: ToolGroupConfig,
        tool_call_ctx: Optional[ToolCallContext] = None,
    ) -> ToolConnection:
        """Get or create a connection for the specified tool group.

        If an task is provided, the connection will be associated with that task.
        If no task is provided, a new connection can be used temporarily, which will be
        closed after use.
        """
        if tool_call_ctx is None:
            return await ToolConnectionFactory.create_connection(
                tool_group_config=tool_group_config
            )

        job_id = tool_call_ctx.job_id
        operator_id = tool_call_ctx.operator_id

        if job_id not in self._connections:
            self._connections[job_id] = {}

        if operator_id not in self._connections[job_id]:
            self._connections[job_id][operator_id] = {}

        if tool_group_id not in self._connections[job_id][operator_id]:
            connection = await ToolConnectionFactory.create_connection(
                tool_group_config=tool_group_config
            )
            self._connections[job_id][operator_id][tool_group_id] = connection
        else:
            connection = self._connections[job_id][operator_id][tool_group_id]
        return connection

    async def release_connection(self, call_tool_ctx: ToolCallContext) -> None:
        """Destroy the specified connection."""
        job_id = call_tool_ctx.job_id
        operator_id = call_tool_ctx.operator_id

        if job_id in self._connections and operator_id in self._connections[job_id]:
            for connection in self._connections[job_id][operator_id].values():
                await connection.close()
            del self._connections[job_id][operator_id]

            # clean up empty job_id entry
            if not self._connections[job_id]:
                del self._connections[job_id]
