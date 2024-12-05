from abc import ABC, abstractmethod
from typing import List
from uuid import uuid4

from app.memory.message import AgentMessage


class ModelService(ABC):
    """Model service."""

    def __init__(self):
        self._id = str(uuid4())

    @abstractmethod
    async def generate(
        self, sys_prompt: str, messages: List[AgentMessage]
    ) -> AgentMessage:
        """Generate a text given a prompt (non-)streaming"""
