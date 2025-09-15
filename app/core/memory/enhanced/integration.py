from __future__ import annotations

from typing import Any

from app.core.memory.enhanced.hook import ReasonerHook
from app.core.reasoner.reasoner import Reasoner
from app.core.model.task import Task
from app.core.memory.reasoner_memory import ReasonerMemory


class EnhancedReasoner(Reasoner):
    """Decorator wrapper adding pre/post hooks to an existing Reasoner.

    Delegates all operations to the wrapped reasoner, inserting hook calls
    around `infer` to support memory retrieval and persistence.
    """

    def __init__(self, inner: Reasoner, hook: ReasonerHook) -> None:
        super().__init__()
        self._inner = inner
        self._hook = hook

    async def infer(self, task: Task) -> str:
        enriched = await self._hook.pre_reasoning(task, self._inner)
        result = await self._inner.infer(enriched)
        await self._hook.post_reasoning(enriched, self._inner)
        return result

    # Delegate the rest of the interface directly
    async def update_knowledge(self, data: Any) -> None:
        return await self._inner.update_knowledge(data)

    async def evaluate(self, data: Any) -> Any:
        return await self._inner.evaluate(data)

    async def conclude(self, reasoner_memory: ReasonerMemory) -> str:
        return await self._inner.conclude(reasoner_memory)

    def init_memory(self, task: Task) -> ReasonerMemory:
        return self._inner.init_memory(task)

    def get_memory(self, task: Task) -> ReasonerMemory:
        return self._inner.get_memory(task)

