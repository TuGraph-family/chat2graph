from typing import Optional, cast

from app.core.common.singleton import Singleton
from app.core.common.type import MessageSourceType, ReasonerType
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.reasoner.reasoner import Reasoner


class ReasonerService(metaclass=Singleton):
    """Reasoner service"""

    def __init__(self):
        self._reasoners: Optional[Reasoner] = None

    def get_reasoner(self) -> Reasoner:
        """Get the reasoner with Memory enhancement if enabled."""
        if not self._reasoners:
            self.init_reasoner(reasoner_type=ReasonerType.DUAL)

        base_reasoner = cast(Reasoner, self._reasoners)

        # Enhance with Memory functionality if available
        try:
            from app.core.memory.enhanced.integration import (
                memory_integration_manager
            )
            return memory_integration_manager.wrap_reasoner(base_reasoner)
        except ImportError:
            # Memory enhancement not available, return base reasoner
            return base_reasoner

    def init_reasoner(
        self,
        reasoner_type: ReasonerType,
        actor_name: Optional[str] = None,
        thinker_name: Optional[str] = None,
    ) -> None:
        """Set the reasoner."""
        if reasoner_type == ReasonerType.DUAL:
            self._reasoners = DualModelReasoner(
                actor_name or MessageSourceType.ACTOR.value,
                thinker_name or MessageSourceType.THINKER.value,
            )
        elif reasoner_type == ReasonerType.MONO:
            self._reasoners = MonoModelReasoner(
                actor_name or MessageSourceType.MODEL.value
            )
        else:
            raise ValueError("Invalid reasoner type.")
