import time
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

from app.agent.reasoner.model_service import ModelService
from app.common.prompt.model_service import FUNC_CALLING_PROMPT
from app.common.system_env import SystemEnv
from app.common.type import MessageSourceType
from app.memory.message import ModelMessage
from app.toolkit.tool.tool import FunctionCallResult, Tool


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
            model_alias=SystemEnv.PROXYLLM_BACKEND,
            api_base=SystemEnv.PROXY_SERVER_URL,
            api_key=SystemEnv.PROXY_API_KEY,
            openai_kwargs={"temperature": SystemEnv.TEMPERATURE},
        )

    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
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
                tools=tools, model_response_text=model_response.text
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

        # convert the conversation messages for DB-GPT LLM
        for message in messages:
            # handle the func call information in the agent message
            base_message_content = message.get_payload()
            func_call_results = message.get_function_calls()
            if func_call_results:
                base_message_content += (
                    "<function_call_result>\n"
                    + "\n".join(
                        [
                            f"{i + 1}. {result.status} called function "
                            f"{result.func_name}:\n"
                            f"Call objective: {result.call_objective}\n"
                            f"Function Output: {result.output}"
                            for i, result in enumerate(func_call_results)
                        ]
                    )
                    + "\n</function_call_result>"
                )

            # Chat2Graph <-> DB-GPT msg: actor <-> ai & thinker <-> human
            if message.get_source_type() == MessageSourceType.ACTOR:
                base_messages.append(AIMessage(content=base_message_content))
            else:
                base_messages.append(HumanMessage(content=base_message_content))

        model_messages = DbgptModelMessage.from_base_messages(base_messages)
        model_request = ModelRequest.build_request(
            model=SystemEnv.PROXYLLM_BACKEND,
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
            source_type=source_type,
            function_calls=func_call_results,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

        return response
