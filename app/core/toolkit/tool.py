from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Literal
from uuid import uuid4


@dataclass
class FunctionCallResult:
    """Tool output."""

    func_name: str
    func_args: Dict[str, Any]
    call_objective: str
    output: str
    status: Literal["succeeded", "failed"] = field(default="succeeded")

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
            status="failed",
        )


@dataclass
class Tool:
    """Tool in the toolkit."""

    name: str
    description: str
    function: Callable
    id: str = field(default_factory=lambda: str(uuid4()))
