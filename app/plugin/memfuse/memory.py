import os
from typing import Any, Dict, List, Optional, Union

from memfuse import AsyncMemFuse, AsyncMemory  # type: ignore

from app.core.common.async_func import run_async_function
from app.core.common.system_env import SystemEnv
from app.core.memory.memory import Memory
from app.core.model.message import ModelMessage


class MemFuseMemory(Memory):
    """MemFuseMemory backed by MemFuse."""

    def __init__(self, job_id: str, operator_id: str) -> None:
        super().__init__()
        self._job_id = job_id
        self._operator_id = operator_id
        # self._client is the AsyncMemFuse client instance
        # self._memory is the initialized MemFuse context for this job & operator

        try:
            # configure MemFuse endpoint via explicit arg
            base_url = SystemEnv.MEMFUSE_BASE_URL
            timeout = SystemEnv.MEMFUSE_TIMEOUT
            api_key = SystemEnv.MEMFUSE_API_KEY
            assert base_url is not None, "MEMFUSE_BASE_URL must be set when ENABLE_MEMFUSE is true"
            # memfuse server does not require api key for now
            # assert api_key is not None, "MEMFUSE_API_KEY must be set when ENABLE_MEMFUSE is true"
            if base_url:
                os.environ["MEMFUSE_BASE_URL"] = str(base_url)
            if api_key:
                os.environ["MEMFUSE_API_KEY"] = str(api_key)
            if timeout:
                os.environ["MEMFUSE_TIMEOUT"] = str(timeout)

            self._client: AsyncMemFuse = AsyncMemFuse(base_url=base_url, timeout=timeout)

            if SystemEnv.PRINT_MEMORY_LOG and base_url:
                print(f"[memory] MemFuse client configured base_url={base_url}, timeout={timeout}")
        except Exception as e:
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuse client init failed: {e}")
            raise ValueError(f"MemFuseMemory initialization failed: {e}") from e

        assert self._client is not None, "MemFuse client must be initialized"

        try:
            # scope by session="chat2graph_..." + self._job_id to isolate reasoner memory
            self._memory: AsyncMemory = run_async_function(
                self._client.init,
                user="chat2graph_" + self._operator_id + self._job_id,
                session="chat2graph_" + self._operator_id + self._job_id,
            )
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuse context ready job={self._job_id} op={self._operator_id}")
        except Exception as e:
            if SystemEnv.PRINT_MEMORY_LOG:
                print(f"[memory] MemFuse init failed: {e}")
            raise ValueError(f"MemFuseMemory initialization failed: {e}") from e

        assert self._memory is not None, "MemFuse memory context must be initialized"

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

    def _retrieve(self, query_text: str, top_k: int) -> List[str]:
        """Retrieve relevant snippets synchronously."""
        if SystemEnv.PRINT_MEMORY_LOG:
            query_preview = query_text[:100] + "..." if len(query_text) > 100 else query_text
            context_type = "reasoner"
            print(
                f"[memory] MemFuseMemory._retrieve: query='{query_preview}' "
                f"top_k={top_k} job={self._job_id} op={self._operator_id} context={context_type}"
            )

        # for operator retrieval, include metadata to filter by task and operator
        query_params = {"query": query_text, "top_k": top_k}

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                "[memory] MemFuseMemory._retrieve: calling self._memory.query with "
                f"params={query_params}"
            )

        resp: Dict[str, Any] = run_async_function(self._memory.query, **query_params)

        if SystemEnv.PRINT_MEMORY_LOG:
            print(f"[memory] MemFuseMemory._retrieve: received response={resp}")

        results = resp.get("data", {}).get("results", [])
        snippets: List[str] = []
        for item in results:
            if isinstance(item, str):
                snippets.append(item)
            elif isinstance(item, dict):
                text = item.get("content") or item.get("text") or item.get("snippet")
                snippets.append(text if isinstance(text, str) else str(item))

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                f"[memory] MemFuseMemory._retrieve: successfully retrieved {len(snippets)} snippets"
            )
            for i, snippet in enumerate(snippets[:2]):  # Show first 2 snippets
                preview = snippet[:100] + "..." if len(snippet) > 100 else snippet
                print(f"[memory] MemFuseMemory._retrieve: result[{i}]: {preview}")
            if len(snippets) > 2:
                print(f"[memory] MemFuseMemory._retrieve: ... and {len(snippets) - 2} more results")

        return snippets

    def _memorize(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a conversation turn."""
        if SystemEnv.PRINT_MEMORY_LOG:
            sys_prompt_preview = sys_prompt[:150] + "..." if len(sys_prompt) > 150 else sys_prompt
            context_type = "reasoner"
            print(f"[memory] MemFuseMemory._memorize: sys_prompt='{sys_prompt_preview}'")

        # convert to OpenAI format with embedded metadata
        oai_messages = self._to_openai_messages(sys_prompt, messages, metadata)

        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                f"[memory] MemFuseMemory._memorize: converted to {len(oai_messages)} "
                "OpenAI format messages"
            )
            for i, oa_msg in enumerate(oai_messages[:2]):  # show first 2 messages
                content_preview = (
                    oa_msg.get("content", "")[:100] + "..."
                    if len(oa_msg.get("content", "")) > 100
                    else oa_msg.get("content", "")
                )
                metadata_info = (
                    f" metadata={oa_msg.get('metadata', {})}" if oa_msg.get("metadata") else ""
                )
                print(
                    f"[memory] MemFuseMemory._memorize: oa_message[{i}] "
                    f"role={oa_msg.get('role', 'unknown')} "
                    f"content='{content_preview}'{metadata_info}"
                )
            if len(oai_messages) > 2:
                print(
                    "[memory] MemFuseMemory._memorize: ... and "
                    f"{len(oai_messages) - 2} more messages"
                )

        # add messages to MemFuse with embedded metadata
        if SystemEnv.PRINT_MEMORY_LOG:
            print(
                "[memory] MemFuseMemory._memorize: calling self._memory.add "
                f"with {len(oai_messages)} messages"
            )
            for i, msg in enumerate(oai_messages):
                content_preview = (
                    msg.get("content", "")[:100] + "..."
                    if len(msg.get("content", "")) > 100
                    else msg.get("content", "")
                )
                metadata_str = f" metadata={msg.get('metadata', {})}" if msg.get("metadata") else ""
                print(
                    f"[memory] MemFuseMemory._memorize: adding message[{i}] "
                    f"role={msg.get('role', 'unknown')} content='{content_preview}'{metadata_str}"
                )

        run_async_function(self._memory.add, oai_messages)

        if SystemEnv.PRINT_MEMORY_LOG:
            context_type = "reasoner"
            metadata_msg = " with embedded metadata" if metadata else " (no metadata)"
            print(
                f"[memory] MemFuseMemory._memorize: successfully added {len(oai_messages)} "
                f"messages to MemFuse{metadata_msg} for {context_type} context"
            )

        return None

    def _to_openai_messages(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[dict]:
        """Convert internal ModelMessage list to OpenAI chat format with optional metadata."""
        max_len = SystemEnv.MEMFUSE_MAX_CONTENT_LENGTH
        out: List[dict] = [{"role": "system", "content": self._truncate(sys_prompt, max_len)}]

        # add metadata to system message if provided
        if metadata:
            out[0]["metadata"] = metadata

        for m in messages:
            msg_dict: Dict[str, Any] = {
                "role": "assistant",
                "content": self._truncate(m.get_payload(), max_len),
            }
            # add metadata to each message if provided
            if metadata:
                msg_dict["metadata"] = metadata
            out.append(msg_dict)
        return out

    def _truncate(self, text: str, max_len: int) -> str:
        if text is None:
            return ""
        return text if len(text) <= max_len else text[: max_len - 3] + "..."
