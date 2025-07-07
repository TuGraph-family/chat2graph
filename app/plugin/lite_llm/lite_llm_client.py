from typing import Any, Dict, List, Optional, Union, cast

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.model.task import ToolCallContext
from app.core.prompt.model_service import FUNC_CALLING_PROMPT
from app.core.reasoner.model_service import ModelService
from app.core.toolkit.tool import FunctionCallResult, Tool


class LiteLlmClient(ModelService):
    """LiteLLM Client.
    Uses LiteLLM to interact with various LLM providers.
    API keys for providers (OpenAI, Anthropic, etc.) should be set as environment variables
    (e.g., OPENAI_API_KEY, ANTHROPIC_API_KEY). LiteLLM will pick them up.
    """

    def __init__(self):
        super().__init__()
        # e.g., "openai/gpt-4o", "anthropic/claude-3-sonnet-20240229"
        # SystemEnv.LLM_ENDPOINT can be used as api_base for custom OpenAI-compatible endpoints
        self._model_alias: str = SystemEnv.LLM_NAME
        self._api_base: str = SystemEnv.LLM_ENDPOINT
        self._api_key: str = SystemEnv.LLM_APIKEY
        self._temperature: float = SystemEnv.TEMPERATURE

        self._max_tokens: int = SystemEnv.MAX_TOKENS
        self._max_completion_tokens: int = SystemEnv.MAX_COMPLETION_TOKENS

    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
        tool_call_ctx: Optional[ToolCallContext] = None,
    ) -> ModelMessage:
        """Generate a text given a prompt using LiteLLM."""
        # prepare model request
        litellm_messages: List[Dict[str, str]] = self._prepare_model_request(
            sys_prompt=sys_prompt, messages=messages, tools=tools
        )

        from litellm import completion
        from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
        from litellm.types.utils import ModelResponse, StreamingChoices

        model_response: Union[ModelResponse, CustomStreamWrapper] = completion(
            model=self._model_alias,
            api_base=self._api_base,
            api_key=self._api_key,
            messages=litellm_messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            max_completion_tokens=self._max_completion_tokens,
            stream=False,
        )
        if isinstance(model_response, CustomStreamWrapper) or isinstance(
            model_response.choices[0], StreamingChoices
        ):
            raise ValueError(
                "Streaming responses are not supported in LiteLlmClient. "
                "Please PR to add a streaming feature."
            )

        # call functions based on the model output
        func_call_results: Optional[List[FunctionCallResult]] = None
        if tools:
            func_call_results = await self.call_function(
                tools=tools,
                model_response_text=cast(str, model_response.choices[0].message.content),
                tool_call_ctx=tool_call_ctx,
            )

        # parse model response to agent message
        response: ModelMessage = self._parse_model_response(
            model_response=model_response,
            messages=messages,
            func_call_results=func_call_results,
        )

        return response

    def _prepare_model_request(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
    ) -> List[Dict[str, str]]:
        """Prepare base messages for the LLM client."""
        if len(messages) == 0:
            raise ValueError("No messages provided.")

        # convert system prompt to system message
        if tools:
            sys_message = sys_prompt + FUNC_CALLING_PROMPT.strip()
        else:
            sys_message = sys_prompt.strip()
        base_messages: List[Dict[str, str]] = [{"role": "system", "content": sys_message}]

        # convert the conversation messages for AiSuite LLM
        for i, message in enumerate(messages):
            # handle the func call information in the agent message
            base_message_content = message.get_payload()
            func_call_results = message.get_function_calls()
            if func_call_results and i >= len(messages) - 2:
                base_message_content += (
                    "<function_call_result>\n"
                    + "\n".join(
                        [
                            f"{i + 1}. {result.status.value} called function "
                            f"{result.func_name}:\n"
                            f"Call objective: {result.call_objective}\n"
                            f"Function Output: {result.output}"
                            for i, result in enumerate(func_call_results)
                        ]
                    )
                    + "\n</function_call_result>"
                )

            # Chat2Graph <-> LiteLLM's last message role should be "user"
            if (len(messages) + i) % 2 == 1:
                base_messages.append({"role": "user", "content": base_message_content.strip()})
            else:
                base_messages.append({"role": "assistant", "content": base_message_content.strip()})

        return base_messages

    def _parse_model_response(
        self,
        model_response: Any,
        messages: List[ModelMessage],
        func_call_results: Optional[List[FunctionCallResult]] = None,
    ) -> ModelMessage:
        """Parse model response to agent message."""

        # determine the source type of the response
        if messages[-1].get_source_type() == MessageSourceType.MODEL:
            source_type = MessageSourceType.MODEL
        elif messages[-1].get_source_type() == MessageSourceType.ACTOR:
            source_type = MessageSourceType.THINKER
        else:
            source_type = MessageSourceType.ACTOR

        response = ModelMessage(
            payload=cast(
                str,
                (
                    model_response.choices[0].message.content or "The LLM response was missing."
                ).strip(),
            ),
            job_id=messages[-1].get_job_id(),
            step=messages[-1].get_step() + 1,
            source_type=source_type,
            function_calls=func_call_results,
        )

        return response
