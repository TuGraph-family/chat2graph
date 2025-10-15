from typing import Optional

from app.core.common.type import ReasonerType
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
