from contextlib import redirect_stdout
from datetime import datetime
import os
from pathlib import Path
from typing import List, Optional

from inspect_ai.model import (
    ChatMessage,
    ChatMessageAssistant,
    ChatMessageSystem,
    ChatMessageTool,
    ChatMessageUser,
    GenerateConfig,
    ModelAPI,
    ModelOutput,
    modelapi,
)
from inspect_ai.model._model_output import ChatCompletionChoice
from inspect_ai.tool import ToolChoice, ToolInfo

from app.core.model.message import HybridMessage, TextMessage
from app.core.sdk.agentic_service import AgenticService


@modelapi(name="chat2graph")
class Chat2GraphModel(ModelAPI):
    """Chat2GraphModel adapter designed to work seamlessly with inspect-ai's Docker sandbox.
    It does NOT perform any file I/O itself. It trusts that the sandbox has prepared
    the environment and passes all paths (e.g., /shared_files/...) directly to the agent.
    """

    def __init__(
        self,
        model_name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_vars: List[str] = [],
        config: GenerateConfig = GenerateConfig(),
        **model_args,
    ) -> None:
        super().__init__(model_name, base_url, api_key, api_key_vars, config)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "gaia_agents.yml")

        self.model_args = model_args
        self.mas = AgenticService.load(config_path)

        self.gaia_files_root = (Path(__file__).parent / "../gaia_files").resolve()
        Path(self.gaia_files_root).mkdir(parents=True, exist_ok=True)

    async def generate(
        self,
        input: list[ChatMessage],
        tools: list[ToolInfo],
        tool_choice: ToolChoice,
        config: GenerateConfig,
    ) -> ModelOutput:
        """Generate a response based on the input chat messages."""
        conversation_text = self._format_conversation_for_chat2graph(input)

        user_message = TextMessage(payload=conversation_text)

        # log file
        log_dir = Path("./run_logs")
        log_dir.mkdir(exist_ok=True)
        log_file_path = log_dir / "gaia_outputs.log"

        with open(log_file_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"--- PROMPT @ {datetime.now()} ---\n{conversation_text}\n\n")
            log_file.flush()

            with redirect_stdout(log_file):
                service_message = self.mas.session().submit(user_message).wait()
                # service_message = TextMessage(payload="Mocked response for testing")

            print("[Chat2Graph] Agent execution finished. stdout redirection ended.")

            # 处理返回结果
            if isinstance(service_message, TextMessage):
                response_payload: str = service_message.get_payload()
            elif isinstance(service_message, HybridMessage):
                text_message = service_message.get_instruction_message()
                response_payload = text_message.get_payload()
            else:
                response_payload = f"UNEXPECTED_RESPONSE_TYPE: {type(service_message)}"

        choice = ChatCompletionChoice(
            message=ChatMessageAssistant(role="assistant", content=response_payload)
        )
        result = ModelOutput(choices=[choice], model=self.model_name)

        return result


    def _format_conversation_for_chat2graph(self, messages: list[ChatMessage]) -> str:
        """Formats the conversation history into a single string."""
        conversation_parts = []
        for message in messages:
            if isinstance(message, ChatMessageSystem):
                conversation_parts.append(f"SYSTEM: {message.content}")
            elif isinstance(message, ChatMessageUser):
                # The user content will have the /shared_files/ path
                conversation_parts.append(f"USER: {message.content}")
            elif isinstance(message, ChatMessageAssistant):
                content = message.content or ""
                conversation_parts.append(f"ASSISTANT: {content}")
            elif isinstance(message, ChatMessageTool):
                conversation_parts.append(f"TOOL_RESULT ({message.function}): {message.text}")
        return "\n\n".join(conversation_parts)
