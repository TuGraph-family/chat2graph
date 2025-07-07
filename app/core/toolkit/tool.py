from dataclasses import dataclass, field
from typing import Any, Callable, Dict
from uuid import uuid4

from app.core.common.type import FunctionCallStatus, ToolType


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
