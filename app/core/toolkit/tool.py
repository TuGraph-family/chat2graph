from dataclasses import dataclass, field
from typing import Any, Callable, Dict
from uuid import uuid4

from app.core.common.type import FunctionCallStatus


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


@dataclass
class Tool:
    """Tool in the toolkit.

    Attributes:
        name: Name of the tool.
        description: Description of the tool, will be shown to the LLM.
        function: Callable function that can be invoked by the LLM.
        id: Unique identifier for the tool, auto-generated if not provided.
    """

    name: str
    description: str
    function: Callable
    id: str = field(default_factory=lambda: str(uuid4()))


@dataclass
class ToolSet(Tool):
    """Base class for tools set, representing the tools that can be called through some protocol.

    Attributes:
        ...
        list_functions: Callable that returns a list of available functions in the tool set.
    """

    list_functions: Callable = lambda: []
