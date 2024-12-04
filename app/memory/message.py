from dataclasses import dataclass
from typing import Literal, Optional
from uuid import uuid4


@dataclass
class AgentMessage:
    """Agent message"""

    sender_id: str
    receiver_id: str
    status: Literal["successed", "failed", "pending", "canceled"]
    content: str
    timestamp: str

    msg_id: str = str(uuid4())
    tool_log: Optional[str] = None
