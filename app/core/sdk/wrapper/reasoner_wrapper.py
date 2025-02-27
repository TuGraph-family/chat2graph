from typing import List, Optional

from app.core.common.type import ReasonerType
from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.job import Job
from app.core.model.message import ModelMessage
from app.core.model.task import Task
from app.core.reasoner.reasoner import Reasoner
from app.core.service.reasoner_service import ReasonerService


class ReasonerWrapper:
    """Facade for Reasoner Model."""

    def __init__(self):
        self._reasoner: Optional[Reasoner] = None

    @property
    def reasoner(self) -> Reasoner:
        """Get the reasoner."""
        if not self._reasoner:
            raise ValueError("Reasoner is not set.")
        return self._reasoner

    def build(self, reasoner_type: ReasonerType) -> "ReasonerWrapper":
        """Set the reasoner of the agent.

        If thinker_name is provided, use DualModelReasoner, otherwise use MonoModelReasoner.
        """
        reasoner_service: ReasonerService = ReasonerService.instance
        reasoner_service.init_reasoner(reasoner_type=reasoner_type)

        return self

    def get_memory(self, job: Job) -> ReasonerMemory:
        """Get the memory of the reasoner."""
        if not self._reasoner:
            raise ValueError("Reasoner is not set.")
        return self._reasoner.get_memory(task=Task(job=job))

    def get_messages(self, job: Job) -> List[ModelMessage]:
        """Get the messages of the reasoner."""
        if not self._reasoner:
            raise ValueError("Reasoner is not set.")
        return self._reasoner.get_memory(task=Task(job=job)).get_messages()

    def get_message_by_index(self, job: Job, index: int) -> ModelMessage:
        """Get a message by index."""
        if not self._reasoner:
            raise ValueError("Reasoner is not set.")
        return self._reasoner.get_memory(task=Task(job=job)).get_message_by_index(index=index)
