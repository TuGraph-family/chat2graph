from abc import ABC, abstractmethod
from typing import Any, List
from uuid import uuid4


class ToolConnection(ABC):
    """Abstract base class representing an active connection to a tool.

    Encapsulates the concrete logic required to invoke tools through different
    connection mechanisms (local package, MCP, etc.).
    """

    def __init__(self):
        self._id = str(uuid4())

    def get_id(self) -> str:
        """Get the unique identifier of the connection."""
        return self._id

    @abstractmethod
    async def call(self, tool_name: str, **kwargs) -> Any:
        """Execute tool call through this connection.

        Args:
            **kwargs: Arguments to pass to the tool

        Returns:
            Result of the tool execution
        """

    @abstractmethod
    async def list_tools(self) -> List[Any]:
        """Get available tool list from connection."""

    @abstractmethod
    async def close(self) -> None:
        """Close and release connection resources."""


class PackageConnection(ToolConnection):
    """Concrete implementation for interacting with ToolPackage tools.

    Handles connections to locally loaded Python packages and modules.
    """

    def __init__(self, runtime_obj: Any):
        super().__init__()
        self._runtime_obj = runtime_obj

    async def call(self, tool_name: str, **kwargs) -> Any:
        """Execute tool call through the package connection."""
        if self._runtime_obj is None:
            raise RuntimeError("Package connection is closed")

        if not callable(self._runtime_obj):
            raise RuntimeError("Runtime object is not callable")
            
        return self._runtime_obj(**kwargs)

    async def list_tools(self) -> List[str]:
        """Get available tool list from the package connection."""
        if self._runtime_obj is None:
            raise RuntimeError("Package connection is closed")

        if hasattr(self._runtime_obj, "list_tools"):
            return await self._runtime_obj.list_tools()
        else:
            return [
                tool
                for tool in dir(self._runtime_obj)
                if callable(getattr(self._runtime_obj, tool))
            ]

    async def close(self) -> None:
        """Close and release package connection resources."""
        self._runtime_obj = None

