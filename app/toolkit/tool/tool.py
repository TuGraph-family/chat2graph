from abc import ABC
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


@dataclass
class Tool(ABC):
    """Tool in the toolkit."""

    function: Callable
    id: str = field(default_factory=lambda: str(uuid4()))
