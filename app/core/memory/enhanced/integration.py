from __future__ import annotations

from typing import Any, List, Optional

from app.core.memory.enhanced.hook import ReasonerHook, OperatorHook
from app.core.reasoner.reasoner import Reasoner
from app.core.model.task import Task
from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.workflow.operator_config import OperatorConfig
from app.core.model.job import Job
from app.core.model.message import WorkflowMessage
from app.core.common.system_env import SystemEnv


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


class EnhancedOperator:
    """Decorator wrapper adding pre/post hooks to an existing Operator.

    Delegates all operations to the wrapped operator, inserting hook calls
    around `execute` to support experience retrieval and persistence.
    """

    def __init__(self, inner, hook: OperatorHook) -> None:
        self._config: OperatorConfig = inner._config
        self._inner = inner
        self._hook = hook

    async def execute(
        self,
        reasoner: Reasoner,
        job: Job,
        workflow_messages: Optional[List[WorkflowMessage]] = None,
        previous_expert_outputs: Optional[List[WorkflowMessage]] = None,
        lesson: Optional[str] = None,
    ) -> WorkflowMessage:
        """Execute the operator with memory hooks."""
        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] EnhancedOperator.execute: starting execution for operator={self._config.id}")

        # Build task first (like the inner operator does)
        task = self._inner._build_task(
            job=job,
            workflow_messages=workflow_messages,
            previous_expert_outputs=previous_expert_outputs,
            lesson=lesson,
        )

        # Pre-execution hook to retrieve experience
        enriched_task = task
        try:
            enriched_task = await self._hook.pre_execute(task)
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] EnhancedOperator.execute: pre_execute hook completed for operator={self._config.id}")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] EnhancedOperator.execute: pre_execute hook failed: {e}")
            # Continue with original task if hook fails

        # Execute the inner operator's reasoning
        result = await reasoner.infer(task=enriched_task)

        # Post-execution hook to persist experience
        try:
            await self._hook.post_execute(enriched_task, result)
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] EnhancedOperator.execute: post_execute hook completed for operator={self._config.id}")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] EnhancedOperator.execute: post_execute hook failed: {e}")
            # Continue even if hook fails

        # Complete the rest of the operator's execute method (MCP cleanup, etc.)
        from app.core.service.tool_connection_service import ToolConnectionService
        tool_connection_service: ToolConnectionService = ToolConnectionService.instance
        await tool_connection_service.release_connection(call_tool_ctx=enriched_task.get_tool_call_ctx())

        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] EnhancedOperator.execute: execution completed for operator={self._config.id}")

        return WorkflowMessage(payload={"scratchpad": result}, job_id=job.id)

    # Delegate other methods
    def get_knowledge(self, job: Job):
        return self._inner.get_knowledge(job)

    def get_env_insights(self):
        return self._inner.get_env_insights()

    def get_id(self) -> str:
        return self._inner.get_id()

    def _build_task(self, *args, **kwargs):
        return self._inner._build_task(*args, **kwargs)