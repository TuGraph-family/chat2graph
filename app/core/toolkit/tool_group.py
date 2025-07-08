from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import uuid4

from app.core.model.task import ToolCallContext
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_config import ToolGroupConfig
from app.core.toolkit.tool_connection import ToolConnection


class ToolGroup(ABC):
    """Base class for tool groups, providing access to tools through various protocols.

    Attributes:
        _id: Unique identifier for the tool group, auto-generated.
        _tool_group_config: Configuration for the tool group, including type and name.
    """

    def __init__(self, tool_group_config: ToolGroupConfig):
        self._id: str = str(uuid4())
        self._tool_group_config: ToolGroupConfig = tool_group_config

    def get_id(self) -> str:
        """Get the unique identifier of the tool group."""
        return self._id

    @abstractmethod
    async def create_connection(
        self, tool_call_ctx: Optional[ToolCallContext] = None
    ) -> ToolConnection:
        """Create a connection to the tool group."""

    @abstractmethod
    async def list_tools(self) -> List[Tool]:
        """List all tools in the group.

        Returns:
            A list of tools available in the group.
        """

class ToolPackage(ToolGroup):
    """ToolPackage represents a set of tools that can be accessed through a local package.

    This is a placeholder implementation for future local tool package support.

    Attributes:
        ...
        _path: Path to the tool package (not implemented).
        _format: Format of the tool package (not implemented).
        _language: Programming language of the tools (not implemented).
    """

    # TODO: implement ToolPackage class to manage tools in a local package

    def __init__(self, tool_group_config: ToolGroupConfig):
        super().__init__(tool_group_config=tool_group_config)
        self._path = None
        self._format = None
        self._language = None

    async def create_connection(
        self, tool_call_ctx: Optional[ToolCallContext] = None
    ) -> ToolConnection:
        """Create a connection to the tool package."""
        raise NotImplementedError("ToolPackage connection creation is not implemented yet.")

    async def list_tools(self) -> List[Tool]:
        """List all tools in the package.

        Returns:
            A list of tools available in the package.
        """
        raise NotImplementedError("ToolPackage tool listing is not implemented yet.")
