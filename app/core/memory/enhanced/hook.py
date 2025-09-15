from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from app.core.common.system_env import SystemEnv
from app.core.env.insight.insight import TextInsight
from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.message import ModelMessage
from app.core.model.task import Task
from app.core.service.memory_service import MemoryService


class ReasonerHook(ABC):
    """Hook interface for enhancing Reasoner with memory operations."""

    @abstractmethod
    async def pre_reasoning(self, task: Task, reasoner) -> Task:
        """Run before reasoning. Can enrich the task and return it."""

    @abstractmethod
    async def post_reasoning(self, task: Task, reasoner) -> None:
        """Run after reasoning. Can persist memory, never raise."""


class NoopReasonerHook(ReasonerHook):
    async def pre_reasoning(self, task: Task, reasoner) -> Task:  # noqa: ARG002
        return task

    async def post_reasoning(self, task: Task, reasoner) -> None:  # noqa: ARG002
        return None


class MemFuseReasonerHook(ReasonerHook):
    """MemFuse-backed hook: inject retrieved snippets and persist turns."""

    async def pre_reasoning(self, task: Task, reasoner) -> Task:  # noqa: ARG002
        if not SystemEnv.ENABLE_MEMFUSE:
            return task
        # requires operator info
        if not task.operator_config:
            return task

        job_id = task.job.id
        operator_id = task.operator_config.id
        query_text = (task.job.goal or "") + (task.job.context or "")
        top_k = SystemEnv.MEMFUSE_RETRIEVAL_TOP_K or 5

        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] pre_reasoning: starting retrieval for job={job_id} op={operator_id}")
            print(f"[memory] pre_reasoning: query_text='{query_text[:100]}{'...' if len(query_text) > 100 else ''}' top_k={top_k}")

        mem_service = MemoryService()
        mem = mem_service.get_or_create_reasoner_memory(job_id, operator_id)

        snippets: List[str] = []
        try:
            # Prefer async retrieval if available
            aretrieve = getattr(mem, "aretrieve", None)
            if callable(aretrieve):  # type: ignore[truthy-function]
                snippets = await aretrieve(query_text, top_k)  # type: ignore[misc]
            else:
                snippets = mem.retrieve(query_text, top_k)

            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] pre_reasoning: retrieved {len(snippets)} snippets from MemFuse")
                for i, snippet in enumerate(snippets[:3]):  # Show first 3 snippets
                    preview = snippet[:150] + "..." if len(snippet) > 150 else snippet
                    print(f"[memory] pre_reasoning: snippet[{i}]: {preview}")
                if len(snippets) > 3:
                    print(f"[memory] pre_reasoning: ... and {len(snippets) - 3} more snippets")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] pre_reasoning retrieval failed: {e}")
            snippets = []

        if snippets:
            content = "[memory]\n" + "\n".join(f"- {s}" for s in snippets if s)
            try:
                if task.insights is None:
                    task.insights = []
                task.insights.append(
                    TextInsight(tags=["memory", "memfuse", f"job:{job_id}", f"op:{operator_id}"], content=content)
                )
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] pre_reasoning: successfully injected {len(snippets)} snippets into task insights")
            except Exception as e:  # noqa: BLE001
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] pre_reasoning inject failed: {e}")
        else:
            if SystemEnv.PRINT_MEMORY_LOG:
                print("[memory] pre_reasoning: no snippets retrieved, task unchanged")

        return task

    async def post_reasoning(self, task: Task, reasoner) -> None:
        if not SystemEnv.ENABLE_MEMFUSE:
            return None
        if not task.operator_config:
            return None

        job_id = task.job.id
        operator_id = task.operator_config.id

        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] post_reasoning: starting memory write for job={job_id} op={operator_id}")

        try:
            # Pull the local history from the underlying reasoner
            reasoner_memory: ReasonerMemory = reasoner.get_memory(task)
            messages: List[ModelMessage] = reasoner_memory.get_messages()

            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] post_reasoning: retrieved {len(messages)} messages from reasoner memory")
                for i, msg in enumerate(messages[:2]):  # Show first 2 messages
                    payload_preview = msg.get_payload()[:100] + "..." if len(msg.get_payload()) > 100 else msg.get_payload()
                    print(f"[memory] post_reasoning: message[{i}]: {payload_preview}")
                if len(messages) > 2:
                    print(f"[memory] post_reasoning: ... and {len(messages) - 2} more messages")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] post_reasoning get messages failed: {e}")
            return None

        # Resolve a reasonable sys prompt approximation
        sys_prompt = self._resolve_sys_prompt(reasoner, task)

        if SystemEnv.PRINT_MEMORY_LOG:
            sys_prompt_preview = sys_prompt[:200] + "..." if len(sys_prompt) > 200 else sys_prompt
            print(f"[memory] post_reasoning: using system prompt: {sys_prompt_preview}")

        try:
            mem_service = MemoryService()
            mem = mem_service.get_or_create_reasoner_memory(job_id, operator_id)
            mem.write_turn(sys_prompt, messages, job_id, operator_id)

            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] post_reasoning: successfully wrote {len(messages)} messages to MemFuse for job={job_id} op={operator_id}")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] post_reasoning write failed: {e}")
        return None

    @staticmethod
    def _resolve_sys_prompt(reasoner, task: Task) -> str:
        try:
            if hasattr(reasoner, "_format_system_prompt"):
                return reasoner._format_system_prompt(task)  # type: ignore[attr-defined]
            if hasattr(reasoner, "_format_actor_sys_prompt"):
                return reasoner._format_actor_sys_prompt(task)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            pass

        # Fallback generic prompt built from base helpers
        try:
            ctx = reasoner._build_task_context(task)  # type: ignore[attr-defined]
            funcs = reasoner._build_func_description(task)  # type: ignore[attr-defined]
            return f"{ctx}\n\n{funcs}"
        except Exception:  # noqa: BLE001
            return ""


# ---------------- Operator Hooks ----------------
class OperatorHook(ABC):
    @abstractmethod
    async def pre_execute(self, task: Task) -> Task:
        """Run before operator execution to enrich task with experience."""

    @abstractmethod
    async def post_execute(self, task: Task, result: str) -> None:
        """Run after operator execution to persist experience."""


class NoopOperatorHook(OperatorHook):
    async def pre_execute(self, task: Task) -> Task:  # noqa: ARG002
        return task

    async def post_execute(self, task: Task, result: str) -> None:  # noqa: ARG002
        return None


class MemFuseOperatorHook(OperatorHook):
    @staticmethod
    def _is_operator_completing(task: Task, operation_result: str) -> bool:
        """Check if the current operator is completing its specific task.

        This focuses on individual operator completion rather than overall job completion.
        An operator is considered complete when it has finished its designated work,
        regardless of whether the job continues with other operators.

        Args:
            task: The task being executed by this operator
            operation_result: The result/output from the operator execution

        Returns:
            bool: True if this operator has completed its work, False otherwise
        """
        if not task.operator_config or not operation_result:
            return False

        job_id = task.job.id
        operator_id = task.operator_config.id

        try:
            completion_indicators = []

            # 1. Check for explicit completion signals in the result
            completion_signals = [
                "TASK_DONE",
                "task is complete",
                "task has been completed",
                "successfully completed",
                "implementation and validated",
                "<deliverable>",
                "</deliverable>",
                "final_output",
                "</final_output>"
            ]

            result_lower = operation_result.lower()
            for signal in completion_signals:
                if signal.lower() in result_lower:
                    completion_indicators.append(f"completion_signal_{signal.replace(' ', '_')}")

            # 2. Check for structured completion markers
            if "<deliverable>" in operation_result and "</deliverable>" in operation_result:
                completion_indicators.append("structured_deliverable")

            if "final_output" in result_lower and ("</final_output>" in operation_result or "deliverable" in result_lower):
                completion_indicators.append("final_output_marker")

            # 3. Assume operator completion if result is substantial and contains conclusion-like patterns
            if len(operation_result.strip()) > 100:  # Substantial result
                conclusion_patterns = [
                    "in conclusion",
                    "to summarize",
                    "summary:",
                    "result:",
                    "output:",
                    "final",
                    "complete",
                    "done",
                    "finished"
                ]

                for pattern in conclusion_patterns:
                    if pattern in result_lower:
                        completion_indicators.append(f"conclusion_pattern_{pattern.replace(' ', '_')}")
                        break  # Only count one conclusion pattern

            # 4. For single-operator tasks, assume completion after execution
            if completion_indicators:
                completion_indicators.append("operator_task_completion")

            is_completing = len(completion_indicators) > 0

            if SystemEnv.PRINT_MEMORY_LOG:
                if is_completing:
                    indicators_str = ", ".join(completion_indicators)
                    print(f"[memory] operator completion detected: job={job_id} op={operator_id} indicators=[{indicators_str}] completing=True")
                else:
                    result_preview = operation_result[:200].replace('\n', ' ') + ("..." if len(operation_result) > 200 else "")
                    print(f"[memory] operator completion check: job={job_id} op={operator_id} result='{result_preview}' completing=False")

            return is_completing

        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] operator completion check failed for job={job_id} op={operator_id}: {e}")
            return False

    async def pre_execute(self, task: Task) -> Task:
        if not SystemEnv.ENABLE_MEMFUSE:
            return task
        if not task.operator_config:
            return task

        job_id = task.job.id
        operator_id = task.operator_config.id

        # Build query from job goal, context, and operator instruction
        instruction = task.operator_config.instruction if task.operator_config else ""
        query_text = f"{task.job.goal or ''} {task.job.context or ''} {instruction}"
        top_k = SystemEnv.MEMFUSE_RETRIEVAL_TOP_K or 5

        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] operator pre_execute: starting experience retrieval for job={job_id} op={operator_id}")
            query_preview = query_text[:100] + "..." if len(query_text) > 100 else query_text
            print(f"[memory] operator pre_execute: query='{query_preview}' top_k={top_k}")

        mem_service = MemoryService()
        mem = mem_service.get_or_create_operator_memory(job_id, operator_id)

        snippets: List[str] = []
        try:
            # Prefer async retrieval if available
            aretrieve = getattr(mem, "aretrieve", None)
            if callable(aretrieve):  # type: ignore[truthy-function]
                snippets = await aretrieve(query_text, top_k, is_operator=True)  # type: ignore[misc]
            else:
                snippets = mem.retrieve(query_text, top_k)

            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] operator pre_execute: retrieved {len(snippets)} experience snippets from MemFuse")
                for i, snippet in enumerate(snippets[:2]):  # Show first 2 snippets
                    preview = snippet[:100] + "..." if len(snippet) > 100 else snippet
                    print(f"[memory] operator pre_execute: experience[{i}]: {preview}")
                if len(snippets) > 2:
                    print(f"[memory] operator pre_execute: ... and {len(snippets) - 2} more experiences")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] operator pre_execute experience retrieval failed: {e}")
            snippets = []

        if snippets:
            content = "[operator_experience]\n" + "\n".join(f"- {s}" for s in snippets if s)
            try:
                if task.insights is None:
                    task.insights = []
                task.insights.append(
                    TextInsight(tags=["operator_experience", "memfuse", f"job:{job_id}", f"op:{operator_id}"], content=content)
                )
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] operator pre_execute: successfully injected {len(snippets)} experience snippets into task insights")
            except Exception as e:  # noqa: BLE001
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] operator pre_execute experience injection failed: {e}")
        else:
            if SystemEnv.PRINT_MEMORY_LOG:
                print("[memory] operator pre_execute: no experience retrieved, task unchanged")

        return task

    async def post_execute(self, task: Task, result: str) -> None:
        if not SystemEnv.ENABLE_MEMFUSE:
            return None
        if not task.operator_config:
            return None

        job_id = task.job.id
        operator_id = task.operator_config.id

        if SystemEnv.PRINT_MEMORY_LOG:
            result_preview = result[:150] + "..." if len(result) > 150 else result
            print(f"[memory] operator post_execute: starting experience write for job={job_id} op={operator_id}")
            print(f"[memory] operator post_execute: result='{result_preview}'")

        # Build a compact system prompt for operator experience
        try:
            instruction = task.operator_config.instruction if task.operator_config else ""
        except Exception:
            instruction = ""
        sys_prompt = (
            "[operator_instruction]\n"
            f"{instruction}\n\n"
            "[job]\n"
            f"goal: {task.job.goal}\n"
            f"context: {task.job.context}"
        )

        if SystemEnv.PRINT_MEMORY_LOG:
            sys_prompt_preview = sys_prompt[:200] + "..." if len(sys_prompt) > 200 else sys_prompt
            print(f"[memory] operator post_execute: sys_prompt='{sys_prompt_preview}'")

        # Create a single assistant message with the execution result
        msg = ModelMessage(payload=result, job_id=job_id, step=1)

        try:
            mem_service = MemoryService()
            mem = mem_service.get_or_create_operator_memory(job_id, operator_id)

            # Check if this operator is completing its task to add task_eos flag
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] operator post_execute: checking operator completion for job={job_id} op={operator_id}")
            is_completing = MemFuseOperatorHook._is_operator_completing(task, result)
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] operator post_execute: operator completion check result: is_completing={is_completing}")

            # Prepare extra metadata for MemFuse write
            extra_metadata = {"task_eos": True} if is_completing else None
            if SystemEnv.PRINT_MEMORY_LOG and extra_metadata:
                print(f"[memory] operator post_execute: will write with extra_metadata={extra_metadata}")

            # Check if MemFuseMemory supports is_operator parameter
            awrite_turn = getattr(mem, "awrite_turn", None)
            if callable(awrite_turn):  # type: ignore[truthy-function]
                # Use enhanced awrite_turn with extra_metadata parameter
                try:
                    await awrite_turn(sys_prompt, [msg], job_id, operator_id, is_operator=True, extra_metadata=extra_metadata)  # type: ignore[misc]
                    if SystemEnv.PRINT_MEMORY_LOG:
                        status_msg = " with task_eos=true" if is_completing else ""
                        print(f"[memory] operator post_execute: successfully wrote experience to MemFuse{status_msg} for job={job_id} op={operator_id}")
                except TypeError:
                    # Fallback for older interface that doesn't support extra_metadata
                    await awrite_turn(sys_prompt, [msg], job_id, operator_id, is_operator=True)  # type: ignore[misc]
                    if SystemEnv.PRINT_MEMORY_LOG:
                        print(f"[memory] operator post_execute: successfully wrote experience to MemFuse (no extra metadata support) for job={job_id} op={operator_id}")
            else:
                mem.write_turn(sys_prompt, [msg], job_id, operator_id)
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] operator post_execute: successfully wrote experience to MemFuse (sync) for job={job_id} op={operator_id}")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] operator post_execute write failed: {e}")
        return None


def get_operator_hook() -> OperatorHook:
    """Factory to get the appropriate operator hook implementation."""
    if SystemEnv.ENABLE_MEMFUSE:
        return MemFuseOperatorHook()
    return NoopOperatorHook()
