from typing import List, Optional

from dbgpt.core import (  # type: ignore
    AIMessage,
    BaseMessage,
    HumanMessage,
    ModelMessage as DbgptModelMessage,
    ModelOutput,
    ModelRequest,
    SystemMessage,
)
from dbgpt.model.proxy.base import LLMClient  # type: ignore
from dbgpt.model.proxy.llms.chatgpt import OpenAILLMClient  # type: ignore

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.model.task import ToolCallContext
from app.core.prompt.model_service import FUNC_CALLING_PROMPT
from app.core.reasoner.model_service import ModelService
from app.core.toolkit.tool import FunctionCallResult, Tool


class DbgptLlmClient(ModelService):
    """DBGPT LLM Client.

    Attributes:
        _llm_client (LLMClient): The LLM client provided by DB-GPT.
    """

    def __init__(self):
        super().__init__()
        # use openai llm client by default
        # TODO: support other llm clients
        # TODO: support more llm client configurations
        self._llm_client: LLMClient = OpenAILLMClient(
            model_alias=SystemEnv.LLM_NAME,
            api_base=SystemEnv.LLM_ENDPOINT,
            api_key=SystemEnv.LLM_APIKEY,
            openai_kwargs={
                "temperature": SystemEnv.TEMPERATURE,
                "max_tokens": SystemEnv.MAX_TOKENS,
                "max_completion_tokens": SystemEnv.MAX_COMPLETION_TOKENS,
            },
        )

    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
        tool_call_ctx: Optional[ToolCallContext] = None,
    ) -> ModelMessage:
        """Generate a text given a prompt."""
        # prepare model request
        model_request: ModelRequest = self._prepare_model_request(
            sys_prompt=sys_prompt, messages=messages, tools=tools
        )

        # generate response using the llm client
        model_response: ModelOutput = await self._llm_client.generate(model_request)

        # call functions based on the model output
        func_call_results: Optional[List[FunctionCallResult]] = None
        if tools:
            func_call_results = await self.call_function(
                tools=tools, model_response_text=model_response.text, tool_call_ctx=tool_call_ctx
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
    ) -> ModelRequest:
        """Prepare base messages for the LLM client."""
        if len(messages) == 0:
            raise ValueError("No messages provided.")

        # convert system prompt to system message
        if tools:
            sys_message = SystemMessage(content=sys_prompt + FUNC_CALLING_PROMPT)
        else:
            sys_message = SystemMessage(content=sys_prompt)
        base_messages: List[BaseMessage] = [sys_message]

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

            # make sure the last message is a human message
            if (len(base_messages) + i) % 2 == 1:
                base_messages.append(HumanMessage(content=base_message_content))
            else:
                base_messages.append(AIMessage(content=base_message_content))

        model_messages = DbgptModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=SystemEnv.LLM_NAME,
            messages=model_messages,
        )

        return model_request

    def _parse_model_response(
        self,
        model_response: ModelOutput,
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
            payload=model_response.text,
            job_id=messages[-1].get_job_id(),
            step=messages[-1].get_step() + 1,
            source_type=source_type,
            function_calls=func_call_results,
        )

        return response
