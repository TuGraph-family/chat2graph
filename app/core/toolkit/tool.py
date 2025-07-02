from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, cast
from uuid import uuid4

from app.core.common.async_func import run_async_function
from app.core.common.type import FunctionCallStatus, ToolType
from app.core.toolkit.mcp_connection import McpConnection
from app.core.toolkit.mcp_service import McpService


@dataclass
class FunctionCallResult:
    """Tool output."""

    func_name: str
    func_args: Dict[str, Any]
    call_objective: str
    output: str
    status: FunctionCallStatus = field(default=FunctionCallStatus.SUCCEEDED)

    @classmethod
    def error(cls, error_message: str) -> "FunctionCallResult":
        """Create a FunctionCallResult instance for error cases.

        Args:
            error_message: The error message to include

        Returns:
            FunctionCallResult configured for error case.
        """
        return cls(
            func_name="",
            func_args={},
            call_objective="",
            output=error_message,
            status=FunctionCallStatus.FAILED,
        )


class Tool:
    """Tool in the toolkit.

    Attributes:
        _id: Unique identifier for the tool, auto-generated.
        _name: Name of the tool.
        _description: Description of the tool, will be shown to the LLM.
        _function: Callable function that can be invoked by the LLM.
        _tool_type: Type of the tool, default is LOCAL_TOOL.
    """

    def __init__(
        self,
        name: str,
        description: str,
        function: Callable,
        tool_type: ToolType = ToolType.LOCAL_TOOL,
    ):
        """Initialize the Tool with name, description, and optional function."""
        self._id: str = str(uuid4())
        self._name: str = name
        self._description: str = description
        self._type: ToolType = tool_type
        self._function: Callable = function

    @property
    def id(self) -> str:
        """Get the unique identifier of the tool."""
        return self._id

    @property
    def name(self) -> str:
        """Get the name of the tool."""
        return self._name

    @property
    def description(self) -> str:
        """Get the description of the tool."""
        return self._description

    @property
    def tool_type(self) -> ToolType:
        """Get the type of the tool."""
        return self._type

    @property
    def function(self) -> Callable:
        """Get the callable function of the tool."""
        return self._function

    def copy(self) -> "Tool":
        """Create a copy of the tool."""
        return Tool(
            name=self._name,
            description=self._description,
            function=self._function,
            tool_type=self._type,
        )


class McpTool(Tool):
    """MCP tool in the toolkit.

    Inherits from Tool and represents a tool that can be used with MCP.
    """

    def __init__(self, name: str, description: str, tool_group: McpService):
        """Initialize the MCP Tool with name, description, and MCP service."""
        super().__init__(
            name=name,
            description=description,
            function=cast(
                Callable,
                run_async_function(self._create_function, name, description, tool_group),
            ),
            tool_type=ToolType.MCP_TOOL,
        )

        self._tool_group = tool_group

        # used to identify the operator id that call tool by connection
        self._operator_id: Optional[str] = None

    def get_tool_group(self) -> McpService:
        """Get the MCP service associated with this tool."""
        return self._tool_group

    def set_operator_id(self, operator_id: str) -> None:
        """Set the operator ID for this tool."""
        self._operator_id = operator_id

    async def _create_function(
        self,
        name: str,
        description: str,
        tool_group: McpService,
    ) -> Callable[..., Any]:
        """Create a placeholder function - actual execution is handled by ToolkitService."""

        async def function(**kwargs) -> Any:
            connection: McpConnection = cast(
                McpConnection, await tool_group.create_connection(self._operator_id)
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
