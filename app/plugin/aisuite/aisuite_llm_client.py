from typing import Any, Dict, List, Optional, cast

from aisuite.client import Client  # type: ignore

from app.core.common.system_env import SystemEnv
from app.core.common.type import MessageSourceType
from app.core.model.message import ModelMessage
from app.core.prompt.model_service import FUNC_CALLING_PROMPT
from app.core.reasoner.model_service import ModelService
from app.core.toolkit.tool import FunctionCallResult, Tool


class AiSuiteLlmClient(ModelService):
    """AiSuite LLM Client.

    Attributes:
        _llm_client (LLMClient): The LLM client provided by AiSuite.
    """

    def __init__(self):
        super().__init__()
        self._llm_client: Client = Client(
            provider_configs={
                "openai": {
                    "api_key": SystemEnv.PROXY_API_KEY,
                    "base_url": SystemEnv.PROXY_SERVER_URL,
                },
                "anthropic": {
                    "api_key": SystemEnv.PROXY_API_KEY,
                    "base_url": SystemEnv.PROXY_SERVER_URL,
                },
                "google": {
                    "api_key": SystemEnv.PROXY_API_KEY,
                    "project_id": SystemEnv.GOOGLE_PROJECT_ID,  # required by Google Vertex AI
                    "region": SystemEnv.GOOGLE_CLOUD_REGION,  # required by Google Vertex AI
                    "application_credentials": SystemEnv.GOOGLE_APPLICATION_CREDENTIALS,  # absolute path  # noqa: E501
                },
            }
        )
        self._model_alias = SystemEnv.PROXYLLM_BACKEND  # ex. "anthropic:claude-3-5-sonnet-20240620"

    async def generate(
        self,
        sys_prompt: str,
        messages: List[ModelMessage],
        tools: Optional[List[Tool]] = None,
    ) -> ModelMessage:
        """Generate a text given a prompt."""
        # prepare model request
        aisuite_messages: List[Dict[str, str]] = self._prepare_model_request(
            sys_prompt=sys_prompt, messages=messages, tools=tools
        )

        # generate response using the llm client
        model_response: Any = self._llm_client.chat.completions.create(
            model=self._model_alias,
            messages=aisuite_messages,
            temperature=SystemEnv.TEMPERATURE,
        )

        # call functions based on the model output
        func_call_results: Optional[List[FunctionCallResult]] = None
        if tools:
            func_call_results = await self.call_function(
                tools=tools,
                model_response_text=cast(str, model_response.choices[0].message.content),
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
        for message in messages:
            # handle the func call information in the agent message
            base_message_content = message.get_payload()
            func_call_results = message.get_function_calls()
            if func_call_results:
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

            # Chat2Graph <-> AISuite msg: actor <-> ai & thinker <-> user
            if message.get_source_type() == MessageSourceType.ACTOR:
                base_messages.append({"role": "assistant", "content": base_message_content.strip()})
            else:
                base_messages.append({"role": "user", "content": base_message_content.strip()})

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
            payload=cast(str, model_response.choices[0].message.content.strip()),
            job_id=messages[-1].get_job_id(),
            step=messages[-1].get_step() + 1,
            source_type=source_type,
            function_calls=func_call_results,
        )

        return response
