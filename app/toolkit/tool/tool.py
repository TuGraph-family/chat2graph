from abc import ABC
from dataclasses import dataclass
from typing import Callable
from uuid import uuid4

from pydantic import BaseModel


@dataclass
class Tool(ABC):
    """Tool in the toolkit."""

    id: str
    function: Callable
    args_schema: BaseModel

    def __init__(self, function: Callable, args_schema: BaseModel):
        self.id = str(uuid4())
        self.function = function
        self.args_schema = args_schema
