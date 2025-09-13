import asyncio
import os
from typing import List, Optional, Union

from app.core.common.system_env import SystemEnv
from app.core.memory.reasoner_memory import ReasonerMemory
from app.core.model.message import ModelMessage


class MemFuseMemory(ReasonerMemory):
    """ReasonerMemory backed by MemFuse SDK.

    - Inherits from ReasonerMemory as requested.
    - Keeps local history for LLM prompts.
    - Uses MemFuse async client for retrieval and persistence.
    - External operations are best-effort and never raise.
    """

    def __init__(self, job_id: str, operator_id: str) -> None:
        super().__init__()
        self._job_id = job_id
        self._operator_id = operator_id
        # Lazy initialize memfuse client to avoid hard dependency when disabled
        self._client: Optional[object] = None
        self._memory = None  # lazily initialized MemFuse memory context

    # ------------------------ Local history ops ------------------------
    def add_message(self, message: ModelMessage) -> None:
        self._history_messages.append(message)

    def remove_message(self) -> None:
        self._history_messages.pop()

    def upsert_message(self, index: int, message: ModelMessage) -> None:
        self._history_messages[index] = message

    def get_messages(self) -> List[ModelMessage]:
        return self._history_messages

    def clear_messages(self) -> None:
        self._history_messages.clear()

    def get_message_by_index(self, index: int) -> ModelMessage:
        return self._history_messages[index]

    def get_message_by_id(self, message_id: str) -> Union[ModelMessage, None]:
        for message in self._history_messages:
            if message.get_id() == message_id:
                return message
        return None

    def get_message_metadata(self, message: ModelMessage) -> dict:
        return message.__dict__

    def get_messages_metadata(self) -> List[dict]:
        return [message.__dict__ for message in self._history_messages]

    # ------------------------ MemFuse ops ------------------------
    async def _ensure_context(self) -> Optional[object]:
        # If feature is off, avoid importing memfuse at all
        if not SystemEnv.ENABLE_MEMFUSE:
            return None

        # Initialize client lazily to avoid ImportError when not installed
        if self._client is None:
            try:
                from memfuse import AsyncMemFuse  # type: ignore
                # Configure SDK endpoint via explicit arg if supported, else env fallback
                base_url = SystemEnv.MEMFUSE_BASE_URL
                timeout = SystemEnv.MEMFUSE_TIMEOUT
                api_key = SystemEnv.MEMFUSE_API_KEY

                # Ensure environment variables are visible to SDKs that auto-read config
                if base_url:
                    os.environ["MEMFUSE_BASE_URL"] = str(base_url)
                if api_key:
                    os.environ["MEMFUSE_API_KEY"] = str(api_key)
                if timeout:
                    os.environ["MEMFUSE_TIMEOUT"] = str(timeout)

                try:
                    # Prefer explicit base_url if AsyncMemFuse supports it
                    self._client = AsyncMemFuse(base_url=base_url, timeout=timeout)  # type: ignore[call-arg]
                except TypeError:
                    # Older SDKs: fall back to default constructor and rely on env vars
                    self._client = AsyncMemFuse()
                if SystemEnv.PRINT_MEMORY_LOG and base_url:
                    print(f"[memory] MemFuse client configured base_url={base_url}")
            except Exception as e:  # noqa: BLE001
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] MemFuse client init failed: {e}")
                return None

        if self._memory is None:
            try:
                # scope by session=job_id to isolate per-job memory
                self._memory = await self._client.init(  # type: ignore[union-attr]
                    user="chat2graph", session=self._job_id
                )
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(
                        f"[memory] MemFuse context ready job={self._job_id} op={self._operator_id}"
                    )
            except Exception as e:  # noqa: BLE001
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] MemFuse init failed: {e}")
                self._memory = None
        return self._memory

    async def aretrieve(self, query_text: str, top_k: int, is_operator: bool = False) -> List[str]:
        if not SystemEnv.ENABLE_MEMFUSE:
            return []

        if SystemEnv.PRINT_MEMORY_LOG:
            query_preview = query_text[:100] + "..." if len(query_text) > 100 else query_text
            context_type = "operator" if is_operator else "reasoner"
            print(f"[memory] MemFuseMemory.aretrieve: query='{query_preview}' top_k={top_k} job={self._job_id} op={self._operator_id} context={context_type}")

        mem = await self._ensure_context()
        if mem is None:
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuseMemory.aretrieve: context unavailable, returning empty results")
            return []
        try:
            # For operator retrieval, include metadata to filter by task and operator
            query_params = {"query": query_text, "top_k": top_k}
            if is_operator:
                query_params["metadata"] = {"task": self._operator_id}
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] MemFuseMemory.aretrieve: using metadata filter for operator context")

            resp = await mem.query(**query_params)
            results = resp.get("data", {}).get("results", [])
            snippets: List[str] = []
            for item in results:
                if isinstance(item, str):
                    snippets.append(item)
                elif isinstance(item, dict):
                    text = (
                        item.get("content")
                        or item.get("text")
                        or item.get("snippet")
                    )
                    snippets.append(text if isinstance(text, str) else str(item))

            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuseMemory.aretrieve: successfully retrieved {len(snippets)} snippets")
                for i, snippet in enumerate(snippets[:2]):  # Show first 2 snippets
                    preview = snippet[:100] + "..." if len(snippet) > 100 else snippet
                    print(f"[memory] MemFuseMemory.aretrieve: result[{i}]: {preview}")
                if len(snippets) > 2:
                    print(f"[memory] MemFuseMemory.aretrieve: ... and {len(snippets) - 2} more results")

            return snippets
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuse query error: {e}")
            return []

    def retrieve(self, query_text: str, top_k: int) -> List[str]:
        # Schedule async retrieval in background; sync callers receive [].
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.aretrieve(query_text, top_k))
        except RuntimeError:
            # Best-effort synchronous call when no loop exists
            try:
                return asyncio.run(self.aretrieve(query_text, top_k))
            except Exception:
                return []
        return []

    async def awrite_turn(
        self, sys_prompt: str, messages: List[ModelMessage], job_id: str, operator_id: str, is_operator: bool = False
    ) -> None:
        if not SystemEnv.ENABLE_MEMFUSE:
            return None

        if SystemEnv.PRINT_MEMORY_LOG:
            sys_prompt_preview = sys_prompt[:150] + "..." if len(sys_prompt) > 150 else sys_prompt
            context_type = "operator" if is_operator else "reasoner"
            print(f"[memory] MemFuseMemory.awrite_turn: writing {len(messages)} messages for job={job_id} op={operator_id} context={context_type}")
            print(f"[memory] MemFuseMemory.awrite_turn: sys_prompt='{sys_prompt_preview}'")

        mem = await self._ensure_context()
        if mem is None:
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuseMemory.awrite_turn: context unavailable, write skipped")
            return None
        try:
            oa_messages = self._to_openai_messages(sys_prompt, messages)

            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuseMemory.awrite_turn: converted to {len(oa_messages)} OpenAI format messages")
                for i, oa_msg in enumerate(oa_messages[:2]):  # Show first 2 messages
                    content_preview = oa_msg.get("content", "")[:100] + "..." if len(oa_msg.get("content", "")) > 100 else oa_msg.get("content", "")
                    print(f"[memory] MemFuseMemory.awrite_turn: oa_message[{i}] role={oa_msg.get('role', 'unknown')} content='{content_preview}'")
                if len(oa_messages) > 2:
                    print(f"[memory] MemFuseMemory.awrite_turn: ... and {len(oa_messages) - 2} more messages")

            # For operator operations, include metadata; for reasoner operations, exclude it
            if is_operator:
                metadata = {"task": operator_id}
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] MemFuseMemory.awrite_turn: using metadata for operator context: {metadata}")
                try:
                    await mem.add(oa_messages, metadata=metadata)  # type: ignore[arg-type]
                    if SystemEnv.PRINT_MEMORY_LOG:
                        print(f"[memory] MemFuseMemory.awrite_turn: successfully added {len(oa_messages)} messages to MemFuse with metadata")
                except TypeError:
                    # Older SDKs may not accept metadata; try without it
                    await mem.add(oa_messages)  # type: ignore[arg-type]
                    if SystemEnv.PRINT_MEMORY_LOG:
                        print(f"[memory] MemFuseMemory.awrite_turn: successfully added {len(oa_messages)} messages to MemFuse (metadata not supported)")
            else:
                # Reasoner operations: no metadata
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] MemFuseMemory.awrite_turn: no metadata for reasoner context")
                await mem.add(oa_messages)  # type: ignore[arg-type]
                if SystemEnv.PRINT_MEMORY_LOG:
                    print(f"[memory] MemFuseMemory.awrite_turn: successfully added {len(oa_messages)} messages to MemFuse (no metadata)")
        except Exception as e:  # noqa: BLE001
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuse add error: {e}")
        return None

    def write_turn(
        self, sys_prompt: str, messages: List[ModelMessage], job_id: str, operator_id: str
    ) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.awrite_turn(sys_prompt, messages, job_id, operator_id))
        except RuntimeError:
            try:
                asyncio.run(self.awrite_turn(sys_prompt, messages, job_id, operator_id))
            except Exception:
                pass
        return None

    # ------------------------ Helpers ------------------------
    def _to_openai_messages(self, sys_prompt: str, messages: List[ModelMessage]) -> List[dict]:
        max_len = SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH or 10000
        out: List[dict] = [{"role": "system", "content": self._truncate(sys_prompt, max_len)}]
        for m in messages:
            out.append({"role": "assistant", "content": self._truncate(m.get_payload(), max_len)})
        return out

    @staticmethod
    def _truncate(text: str, max_len: int) -> str:
        if text is None:
            return ""
        return text if len(text) <= max_len else text[: max_len - 3] + "..."
