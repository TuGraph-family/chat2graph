from typing import Dict

from app.core.common.singleton import Singleton
from app.core.common.system_env import SystemEnv
from app.core.memory.reasoner_memory import (
    BuiltinReasonerMemory,
    ReasonerMemory,
)


class MemoryService(metaclass=Singleton):
    """Centralized memory service (singleton).

    Manages in-process reasoner/operator memories keyed by job and operator.
    Chooses memory implementation based on feature toggles, with a safe fallback
    to builtin in-memory storage when MemFuse is disabled or unavailable.
    """

    def __init__(self) -> None:
        # job_id -> operator_id -> ReasonerMemory
        self._reasoner_memories: Dict[str, Dict[str, ReasonerMemory]] = {}
        self._operator_memories: Dict[str, Dict[str, ReasonerMemory]] = {}

    def get_or_create_reasoner_memory(self, job_id: str, operator_id: str) -> ReasonerMemory:
        """Get or create a ReasonerMemory instance for a job/operator pair."""
        if job_id not in self._reasoner_memories:
            self._reasoner_memories[job_id] = {}
        if operator_id not in self._reasoner_memories[job_id]:
            self._reasoner_memories[job_id][operator_id] = self._create_memory(job_id, operator_id)
        return self._reasoner_memories[job_id][operator_id]

    def get_or_create_operator_memory(self, job_id: str, operator_id: str) -> ReasonerMemory:
        """Get or create an Operator memory instance for a job/operator pair."""
        if job_id not in self._operator_memories:
            self._operator_memories[job_id] = {}
        if operator_id not in self._operator_memories[job_id]:
            self._operator_memories[job_id][operator_id] = self._create_memory(job_id, operator_id)
        return self._operator_memories[job_id][operator_id]

    def _create_memory(self, job_id: str, operator_id: str) -> ReasonerMemory:
        """Create a memory implementation based on SystemEnv flags.

        If `ENABLE_MEMFUSE` is set, try to create a MemFuse-backed memory; otherwise
        or on any import/creation failure, fall back to `BuiltinReasonerMemory`.
        """
        if SystemEnv.ENABLE_MEMFUSE:
            try:
                # Lazy import to avoid hard dependency if not enabled yet
                from app.core.memory.memfuse_memory import MemFuseMemory  # type: ignore

                if SystemEnv.PRINT_MEMORY_LOG:
                    print(
                        f"[memory] MemoryService: creating MemFuseMemory for job={job_id} operator={operator_id}"
                    )
                return MemFuseMemory(job_id=job_id, operator_id=operator_id)
            except Exception as e:  # noqa: BLE001
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(
                        f"[memory] MemoryService: MemFuseMemory unavailable, falling back to BuiltinReasonerMemory. Error: {e}"
                    )
        # fallback
        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] MemoryService: creating BuiltinReasonerMemory for job={job_id} operator={operator_id}")
        return BuiltinReasonerMemory()
