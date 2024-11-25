from abc import ABC
from dataclasses import dataclass
from typing import Callable, Optional, Type
from uuid import uuid4

from pydantic import BaseModel


@dataclass
class Tool(ABC):
    """Tool in the toolkit."""

    id: str
    function: Callable
    args_schema: Type[BaseModel]

    def __init__(
        self,
        function: Callable,
        args_schema: Type[BaseModel],
        tool_id: Optional[str] = None,
    ):
        self.id = tool_id or str(uuid4())
        self.function = function
        self.args_schema = args_schema
