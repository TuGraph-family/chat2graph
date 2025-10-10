from typing import List

from app.core.common.system_env import SystemEnv
from app.core.env.insight.insight import Insight, TextInsight
from app.core.model.message import ModelMessage
from app.core.model.task import MemoryKey
from app.plugin.memfuse.memory import MemFuseMemory


class MemFuseReasonerMemory(MemFuseMemory):
    """ReasonerMemory backed by MemFuse."""

    def retrieve(self, memory_key: MemoryKey, query_text: str) -> List[Insight]:
        """Retrieve relevant past experiences for the reasoner before execution."""
        job_id = memory_key.job_id
        operator_id = memory_key.operator_id
        top_k = SystemEnv.MEMFUSE_RETRIEVAL_TOP_K

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                f"[memory] operator retrieve: starting experience retrieval for "
                f"job={job_id} op={operator_id}"
            )
            query_preview = query_text[:100] + "..." if len(query_text) > 100 else query_text
            print(f"[memory] operator retrieve: query='{query_preview}' top_k={top_k}")

        snippets = self._retrieve(query_text, top_k)

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                f"[memory] operator retrieve: retrieved {len(snippets)} experience snippets "
                "from MemFuse"
            )
            for i, snippet in enumerate(snippets[:2]):  # show first 2 snippets
                preview = snippet[:100] + "..." if len(snippet) > 100 else snippet
                print(f"[memory] operator retrieve: experience[{i}]: {preview}")
            if len(snippets) > 2:
                print(
                    f"[memory] operator retrieve: ... and {len(snippets) - 2} more experiences"
                )

        insights: List[Insight] = []
        if len(snippets) > 0:
            content = "[reasoner_experience]\n" + "\n".join(f"- {s}" for s in snippets if s)
            insights.append(
                TextInsight(
                    tags=[
                        "reasoner_experience",
                        "memfuse",
                        f"job:{job_id}",
                        f"op:{operator_id}",
                    ],
                    content=content,
                )
            )
            if SystemEnv.PRINT_MEMORY_LOG:
                print(
                    f"[memory] operator retrieve: successfully injected {len(snippets)} "
                    "experience snippets into task insights"
                )
        else:
            if SystemEnv.PRINT_MEMORY_LOG:
                print("[memory] operator retrieve: no experience retrieved, task unchanged")

        return insights

    def memorize(self, memory_key: MemoryKey, memory_text: str, result: str) -> None:
        """Memorize the reasoner's execution result after execution."""
        job_id = memory_key.job_id
        operator_id = memory_key.operator_id

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                "[memory] operator memorize: starting experience write for "
                f"job={job_id} op={operator_id}"
            )
            memory_text_preview = (
                memory_text[:200] + "..." if len(memory_text) > 200 else memory_text
            )
            print(f"[memory] operator memorize: memory_text='{memory_text_preview}'")

        # create a single assistant message with the execution result
        msg = ModelMessage(payload=result, job_id=job_id, step=1)

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                "[memory] operator memorize: checking operator completion for "
                f"job={job_id} op={operator_id}"
            )

        # prepare extra metadata for MemFuse write
        extra_metadata = {"task_eos": True}
        if SystemEnv.PRINT_MEMORY_LOG and extra_metadata:
            print(
                f"[memory] operator memorize: will write with extra_metadata={extra_metadata}"
            )

        self._memorize(memory_text, [msg], extra_metadata)
        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                "[memory] operator memorize: successfully wrote experience to MemFuse (sync) "
                f"for job={job_id} op={operator_id}"
            )
