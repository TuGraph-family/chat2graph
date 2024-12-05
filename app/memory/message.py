from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import uuid4

from app.commom.type import MessageSourceType


@dataclass
class Message:
    """Message"""

    content: str
    timestamp: str
    message_id: str = str(uuid4())


@dataclass
class AgentMessage(Message):
    """Agent message"""

    source_type: MessageSourceType = MessageSourceType.MODEL
    function: Optional[Dict[str, Any]] = None
    tool_log: Optional[str] = None


@dataclass
class UserMessage(Message):
    """User message"""

    # TODO: Add user message attributes
