from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional
from uuid import uuid4


@dataclass
class Message:
    """Message"""

    sender: str
    content: str
    timestamp: str
    message_id: str = str(uuid4())


@dataclass
class AgentMessage(Message):
    """Agent message"""

    sender: Literal["Thinker", "Actor", "Reasoner"]
    function: Optional[Dict[str, Any]] = None
    tool_log: Optional[str] = None


@dataclass
class UserMessage(Message):
    """User message"""

    # TODO: Add user message attributes
