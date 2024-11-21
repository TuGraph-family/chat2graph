from dataclasses import dataclass
from typing import Literal


@dataclass
class AgentMessage:
    """Agent message"""

    msg_id: str
    sender_id: str
    receiver_id: str
    status: Literal["successed", "failed", "pending", "canceled"]
    content: str
    timestamp: str

    tool_log: str = None
