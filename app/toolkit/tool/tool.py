from dataclasses import dataclass


@dataclass
class Tool:
    """The tool in the toolkit."""

    id: str
    function: callable
