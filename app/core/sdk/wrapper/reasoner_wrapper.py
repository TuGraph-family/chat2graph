from typing import List, Optional

from app.core.common.type import MessageSourceType
from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.job import Job
from app.core.model.message import ModelMessage
from app.core.model.task import Task
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.reasoner.reasoner import Reasoner


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

    def build(
        self, actor_name: str = MessageSourceType.MODEL.value, thinker_name: Optional[str] = None
    ) -> "ReasonerWrapper":
        """Set the reasoner of the agent.

        If thinker_name is provided, use DualModelReasoner, otherwise use MonoModelReasoner.
        """
        if thinker_name:
            self._reasoner = DualModelReasoner(actor_name=actor_name, thinker_name=thinker_name)
        else:
            self._reasoner = MonoModelReasoner(model_name=actor_name)

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
