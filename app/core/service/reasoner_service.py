from typing import Optional, cast

from app.core.common.singleton import Singleton
from app.core.common.type import MessageSourceType, ReasonerType
from app.core.reasoner.dual_model_reasoner import DualModelReasoner
from app.core.reasoner.mono_model_reasoner import MonoModelReasoner
from app.core.reasoner.reasoner import Reasoner
from app.core.common.system_env import SystemEnv

# Enhanced memory wrapper and hooks
try:
    from app.core.memory.enhanced import EnhancedReasoner, MemFuseReasonerHook, NoopReasonerHook
except Exception:  # noqa: BLE001
    EnhancedReasoner = None  # type: ignore[assignment]
    MemFuseReasonerHook = None  # type: ignore[assignment]
    NoopReasonerHook = None  # type: ignore[assignment]


class ReasonerService(metaclass=Singleton):
    """Reasoner service"""

    def __init__(self):
        self._reasoners: Optional[Reasoner] = None

    def get_reasoner(self) -> Reasoner:
        """Get the reasoner."""
        if not self._reasoners:
            self.init_reasoner(reasoner_type=ReasonerType.DUAL)
        return cast(Reasoner, self._reasoners)

    def init_reasoner(
        self,
        reasoner_type: ReasonerType,
        actor_name: Optional[str] = None,
        thinker_name: Optional[str] = None,
    ) -> None:
        """Set the reasoner."""
        if reasoner_type == ReasonerType.DUAL:
            base = DualModelReasoner(
                actor_name or MessageSourceType.ACTOR.value,
                thinker_name or MessageSourceType.THINKER.value,
            )
        elif reasoner_type == ReasonerType.MONO:
            base = MonoModelReasoner(actor_name or MessageSourceType.MODEL.value)
        else:
            raise ValueError("Invalid reasoner type.")

        # Conditionally wrap with enhanced memory when enabled and available
        if SystemEnv.ENABLE_MEMFUSE and EnhancedReasoner and MemFuseReasonerHook and NoopReasonerHook:  # type: ignore[truthy-bool]
            hook = MemFuseReasonerHook()  # type: ignore[call-arg]
            self._reasoners = EnhancedReasoner(base, hook)  # type: ignore[call-arg]
        else:
            self._reasoners = base
