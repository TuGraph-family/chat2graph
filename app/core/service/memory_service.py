from typing import Dict

from app.core.common.singleton import Singleton
from app.core.common.system_env import SystemEnv
from app.core.memory.memory import BuiltinMemory, Memory
from app.core.model.task import MemoryKey
from app.plugin.memfuse.operator_memory import MemFuseOperatorMemory
from app.plugin.memfuse.reasoner_memory import MemFuseReasonerMemory


class MemoryService(metaclass=Singleton):
    """Centralized memory service (singleton).

    Manages in-process reasoner/operator memories keyed by job and operator.
    Chooses memory implementation based on feature toggles, with a safe fallback
    to builtin in-memory storage when MemFuse is disabled or unavailable.
    """

    def __init__(self) -> None:
        # job_id -> operator_id -> ReasonerMemory
        self._reasoner_memories: Dict[str, Dict[str, Memory]] = {}
        self._operator_memories: Dict[str, Dict[str, Memory]] = {}

    async def get_or_create_reasoner_memory(self, reasoner_memory_key: MemoryKey) -> Memory:
        """Get or create a ReasonerMemory instance for a job/operator pair.

        If `ENABLE_MEMFUSE` is set, create a MemFuse-backed memory.
        """
        job_id = reasoner_memory_key.job_id
        operator_id = reasoner_memory_key.operator_id
        if job_id not in self._reasoner_memories:
            self._reasoner_memories[job_id] = {}
        if operator_id not in self._reasoner_memories[job_id]:
            if SystemEnv.ENABLE_MEMFUSE:
                memory = MemFuseReasonerMemory(job_id=job_id, operator_id=operator_id)
                await memory.initialize()
                self._reasoner_memories[job_id][operator_id] = memory
            else:
                self._reasoner_memories[job_id][operator_id] = BuiltinMemory()
        return self._reasoner_memories[job_id][operator_id]

    async def get_or_create_operator_memory(self, operator_memory_key: MemoryKey) -> Memory:
        """Get or create an Operator memory instance for a job/operator pair.

        If `ENABLE_MEMFUSE` is set, create a MemFuse-backed memory.
        """
        job_id = operator_memory_key.job_id
        operator_id = operator_memory_key.operator_id
        if job_id not in self._operator_memories:
            self._operator_memories[job_id] = {}
        if operator_id not in self._operator_memories[job_id]:
            if SystemEnv.ENABLE_MEMFUSE:
                memory = MemFuseOperatorMemory(job_id=job_id, operator_id=operator_id)
                await memory.initialize()
                self._operator_memories[job_id][operator_id] = memory
            else:
                self._operator_memories[job_id][operator_id] = BuiltinMemory()
        return self._operator_memories[job_id][operator_id]
