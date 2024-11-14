from abc import ABC
from dataclasses import dataclass
from typing import Callable
from uuid import uuid4


@dataclass
class Tool(ABC):
    """The tool in the toolkit."""

    id: str
    function: Callable

    def __init__(self, function: Callable):
        self.id = str(uuid4())
        self.function = function
