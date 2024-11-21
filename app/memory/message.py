from dataclasses import dataclass
from typing import Literal
from uuid import uuid4


@dataclass
class AgentMessage:
    """Agent message dataclass"""

    sender_id: str
    receiver_id: str
    status: Literal["successed", "failed", "pending", "canceled"]
    content: str
    timestamp: str

    msg_id: str = str(uuid4())
    op_id: str = None
    tool_log: str = None
