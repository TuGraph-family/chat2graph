import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

import google.generativeai as genai
from google.generativeai.generative_models import ChatSession
from mcp.types import EmbeddedResource, ImageContent, TextContent

from app.core.common.system_env import SystemEnv
from app.core.common.util import parse_jsons
from app.core.model.task import ToolCallContext
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.mcp.mcp_service import McpService
from app.core.toolkit.system_tool.url_downloader import UrlDownloaderTool
from app.core.toolkit.tool import Tool


class BrowserReadAndGetStateTool(Tool):
    """An intelligent tool that analyzes a webpage using a conversational VLM to
    determine the single best next step towards a user's goal. It can answer
    questions directly, find partial information while recommending interaction
    to get more, or identify the exact element for the next interaction.
    """

    def __init__(self):
        super().__init__(
            name=self.browser_read_and_get_state.__name__,
            description=self.browser_read_and_get_state.__doc__ or "",
            function=self.browser_read_and_get_state,
        )

    async def browser_read_and_get_state(
        self,
        tool_call_ctx: ToolCallContext,
        vlm_task: str,
        task_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyzes the current webpage to determine the single best next step towards a user's goal.

        This is a powerful visual analysis tool. In a multi-step task, you should call this tool
        repeatedly after each action (like a click or scroll) to re-evaluate the new page state.

        **When to use this tool:**
        Use this tool as your primary 'eyes' to understand a webpage. Call it after navigating to a
        new page, or after performing an action that changes the page content.

        **Strategy for Multi-Step Tasks:**
        This tool supports conversational context to become more efficient and accurate over time.
        - **First Call:** On a new page, use ONLY the `vlm_task` parameter to describe the overall goal.
        - **Subsequent Calls:** After performing an action (e.g., dismissing a pop-up, clicking 'next page'),
          call this tool again. This time, provide BOTH:
            1. `vlm_task`: The SAME overall goal.
            2. `task_context`: A brief summary of the last action and the current situation.
          This helps the VLM understand the progress and not get confused.

        **How to formulate `vlm_task` and `task_context`:**

        *   **`vlm_task` (The Unchanging Goal):**
            - "Find and book the cheapest flight from JFK to LAX for tomorrow."
            - "Summarize the return policy of this product."
            - "Find the number of publications by author X published before 2020."

        *   **`task_context` (The Evolving Situation):**
            - *After dismissing a cookie banner:* "I have just dismissed the cookie banner. Now I need to see the main content."
            - *After clicking 'next page':* "I am now on page 2 of the search results. I need to continue my search here."
            - *In your ORCID example:* "I am on the second page of the author's works. I already counted 28 pre-2020 publications on the first page. Now I need to count the ones on this page."

        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "vlm_task": {
                    "type": "string",
                    "description": "The user's unchanging, high-level goal. Describe what you ultimately want to achieve on this website."
                },
                "task_context": {
                    "type": "string",
                    "description": "Optional. A summary of what has already been accomplished or the current state of the multi-step task. Use this on all calls after the first one.",
                    "default": null
                }
            },
            "required": ["vlm_task"]
        }
        """  # noqa: E501
        mcp_service = self._get_mcp_service()
        mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)
        temp_dir = "./.gaia_tmp/"
        os.makedirs(temp_dir, exist_ok=True)

        gemini_conversation = ConversationalGeminiChat()
        chat_session = gemini_conversation.start_chat()

        try:
            # === Turn 1: Triage Phase with Clean Screenshot ===
            clean_results = await mcp_connection.call(
                tool_name="browser_read_and_get_state",
                include_screenshot=True,
                screenshot_with_highlighted_elements=False,
            )
            _, clean_screenshot_base64 = self._parse_mcp_results(clean_results)
            clean_screenshot_path = self._save_screenshot(
                clean_screenshot_base64, temp_dir, "clean"
            )

            triage_prompt = self._get_triage_prompt(vlm_task, task_context)
            triage_vlm_result_str = await gemini_conversation.send_message_in_chat(
                chat=chat_session, query_prompt=triage_prompt, media_paths=[clean_screenshot_path]
            )

            triage_result = self._parse_vlm_json_output(triage_vlm_result_str)
            action_type = triage_result.get("next_action_type")

            base_response: Dict[str, Any] = {
                "triage_analysis": triage_result,
                "original_screenshot": clean_screenshot_path,
            }

            # === Decision Logic Based on Triage ===
            if action_type in ["ANSWER", "NAVIGATE_OR_SEARCH", "CLARIFY"]:
                return self._format_terminal_response(action_type, triage_result, base_response)

            elif action_type == "INTERACT":
                # === Turn 2: Execution Phase with Highlighted Screenshot ===
                highlighted_results = await mcp_connection.call(
                    tool_name="browser_read_and_get_state",
                    include_screenshot=True,
                    screenshot_with_highlighted_elements=True,
                )
                highlighted_page_state, highlighted_screenshot_base64 = self._parse_mcp_results(
                    highlighted_results
                )
                highlighted_screenshot_path = self._save_screenshot(
                    highlighted_screenshot_base64, temp_dir, "highlighted"
                )

                execution_prompt = self._get_conversational_execution_prompt(highlighted_page_state)
                execution_vlm_result_str = await gemini_conversation.send_message_in_chat(
                    chat=chat_session,
                    query_prompt=execution_prompt,
                    media_paths=[highlighted_screenshot_path],
                )

                execution_result = self._parse_vlm_json_output(execution_vlm_result_str)
                return self._format_interaction_response(
                    triage_result, execution_result, base_response, highlighted_screenshot_path
                )

            else:
                return self._format_error_response(
                    f"Unknown action type: {action_type}",
                    triage_vlm_result_str,
                    clean_screenshot_path,
                )

        except (ValueError, json.JSONDecodeError) as e:
            return self._format_error_response(f"An error occurred during processing: {e}", "", "")
        except Exception as e:
            return self._format_error_response(f"An unexpected exception occurred: {e}", "", "")
        finally:
            gemini_conversation.cleanup_temp_files()

    # --- Helper and Prompt Methods ---

    def _get_mcp_service(self) -> McpService:
        """Get the MCP service instance for browser interactions."""
        # implementation to get MCP service
        toolkit_service: ToolkitService = ToolkitService.instance
        toolkit = toolkit_service.get_toolkit()
        for item_id in toolkit.vertices():
            tool_group = toolkit.get_tool_group(item_id)
            if (
                tool_group
                and isinstance(tool_group, McpService)
                and tool_group._tool_group_config.name == "BrowserTool"
            ):
                return tool_group
        raise ValueError("MCP service (BrowserTool) not registered in the toolkit.")

    def _parse_mcp_results(
        self,
        results: List[Union[TextContent, ImageContent, EmbeddedResource]],
    ) -> Tuple[Dict[str, Any], str]:
        """Parses MCP results to extract page state and screenshot."""
        if not results or not isinstance(results[0], TextContent):
            raise ValueError("Expected a text content block with page state info.")
        page_state = json.loads(results[0].text)
        screenshot_base64 = page_state.get("screenshot")
        if not screenshot_base64:
            raise ValueError("Screenshot not found in the page state.")
        return page_state, screenshot_base64

    def _save_screenshot(self, b64_string: str, directory: str, prefix: str) -> str:
        """Saves a base64-encoded screenshot to a file."""
        path = os.path.join(directory, f"{prefix}_{uuid.uuid4()}.png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64_string))
        print(f"Screenshot saved to {path}")
        return path

    def _parse_vlm_json_output(self, vlm_result: str) -> Dict[str, Any]:
        """Parses the VLM's JSON output, ensuring it's valid JSON."""
        result_jsons = parse_jsons(vlm_result)
        if not result_jsons or isinstance(result_jsons[0], json.JSONDecodeError):
            raise ValueError(f"VLM did not return a valid JSON. Output: {vlm_result}")
        return result_jsons[0]

    def _format_terminal_response(
        self,
        action_type: str,
        triage_result: Dict[str, Any],
        base_response: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Formats the final response for terminal actions."""
        return {
            **base_response,
            "status": "COMPLETED" if action_type == "ANSWER" else "ACTION_NEEDED",
            "result_type": action_type,
            "data": {"answer": triage_result.get("final_answer", triage_result.get("reasoning"))},
        }

    def _format_interaction_response(
        self,
        triage_result: Dict[str, Any],
        execution_result: Dict[str, Any],
        base_response: Dict[str, Any],
        highlighted_screenshot_path: str,
    ):
        """Formats the final response for interaction actions."""
        final_data = {"interaction_recommendation": execution_result.get("recommendation")}
        if triage_result.get("information_status") == "PARTIAL":
            final_data["partial_answer"] = triage_result.get("partial_answer")

        return {
            **base_response,
            "status": "ACTION_NEEDED",
            "result_type": "INTERACT",
            "information_status": triage_result.get("information_status", "NOT_APPLICABLE"),
            "data": final_data,
            "highlighted_screenshot": highlighted_screenshot_path,
        }

    def _format_error_response(
        self,
        message: str,
        vlm_output: str,
        screenshot_path: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Formats an error response."""
        response = context or {}
        response.update(
            {
                "status": "ERROR",
                "error_message": message,
                "vlm_output": vlm_output,
            }
        )
        if (
            screenshot_path
            and "original_screenshot" not in response
            and "highlighted_screenshot" not in response
        ):
            response["screenshot"] = screenshot_path
        return response

    def _get_triage_prompt(
        self,
        vlm_task: str,
        task_context: Optional[str] = None,
    ) -> str:
        """Generates the triage prompt for the VLM."""

        base_prompt = f'''As an expert web agent, analyze this clean webpage screenshot to determine the strategy for the user's goal.

User's ultimate goal: "{vlm_task}"'''  # noqa: E501

        if task_context:
            base_prompt += f'''
**Current Task Context:** You are not starting from scratch. Here is what has happened so far:
"{task_context}"'''  # noqa: E501

        base_prompt += """
Your Task: Triage the situation with nuance. Is the goal about finding information or performing an action?

1.  **Blocker First:** Always check for blocking elements (cookie banners, popups). If present, the goal is to interact and dismiss it.
2.  **Goal Analysis:**
    *   **Information-Seeking Goal?** (e.g., "What is...", "Find...", "Summarize...")
        *   Can you find the COMPLETE answer on the screen?
        *   Can you find a PARTIAL answer, with clear indication that more is available after an interaction (e.g., "Next Page", "Read More", expanding a section)?
        *   Is the information COMPLETELY HIDDEN behind an interactive element (e.g., a "Details" tab)?
    *   **Action-Oriented Goal?** (e.g., "Log in", "Search for", "Click on...")
        *   Is the target element for the action visible and ready?

3.  **Final Classification:** Based on your analysis, classify the situation.

Respond with a SINGLE JSON object with NO MARKDOWN formatting. Schema:
{
  "page_summary": "A brief, one-sentence description of the page's content and purpose.",
  "reasoning": "Your detailed step-by-step thinking. First, blocker check. Second, analyze the user's goal type (info or action). Third, assess information availability on screen. Finally, conclude the action type and info status.",
  "next_action_type": "Choose ONE: 'ANSWER' | 'INTERACT' | 'NAVIGATE_OR_SEARCH' | 'CLARIFY'",
  "information_status": "Choose ONE: 'COMPLETE' | 'PARTIAL' | 'NOT_FOUND' | 'NOT_APPLICABLE' (Use for non-info goals like clicking a login button).",
  "final_answer": "If information_status is 'COMPLETE', provide the full answer here. Otherwise, empty string.",
  "partial_answer": "If information_status is 'PARTIAL', provide the extracted partial information here. Otherwise, empty string.",
  "interaction_target_description": "If next_action_type is 'INTERACT', describe the target element needed to proceed (e.g., 'the `Next Page` button at the bottom', 'the `+` icon next to Shipping Policy', 'the main search input field'). Otherwise, empty string."
}"""  # noqa: E501
        return base_prompt

    def _get_conversational_execution_prompt(self, page_state: Dict[str, Any]) -> str:
        """Generates the execution prompt for the VLM based on highlighted elements."""
        page_state_without_screenshot = page_state.copy()
        page_state_without_screenshot.pop("screenshot", None)

        return f"""Perfect, that makes sense. Based on your previous analysis, I have now highlighted the interactive elements on the page. Here is the new screenshot and the corresponding JSON data.

Please identify the exact `element_index` for the target you described in your last message.

Interactive Elements JSON:
{json.dumps(page_state_without_screenshot, indent=2)}

Your task is now purely tactical: find the element number. If it's an input field, also determine the `value` to type based on our original goal.

Respond with a SINGLE JSON object with NO MARKDOWN formatting. Schema:
{{
  "thinking": "Confirming my previous assessment with the highlighted view. The element I described as '...' corresponds to index X because...",
  "recommendation": {{
    "element_index": <Integer>,
    "value": "String to type if needed, otherwise empty",
    "ambiguous_options": [<Integer>]
  }}
}}"""  # noqa: E501


class ConversationalGeminiChat:
    """Manages a multi-turn conversational session with the Google Gemini API,
    specializing in multi-modal inputs. This is a stateful tool designed to be
    used within a single, coherent operation.
    """

    def __init__(self):
        try:
            genai.configure(api_key=SystemEnv.MULTI_MODAL_LLM_APIKEY)
            self.model = genai.GenerativeModel(model_name=SystemEnv.MULTI_MODAL_LLM_NAME)
        except Exception as e:
            raise RuntimeError(
                "Failed to configure Google Generative AI. Check API key and environment variables."
            ) from e
        self.temp_files_to_clean: List[Path] = []

    def start_chat(self) -> ChatSession:
        """Starts a new chat session."""
        print("Starting a new Gemini chat session...")
        return self.model.start_chat()

    async def send_message_in_chat(
        self,
        chat: ChatSession,
        query_prompt: str,
        media_paths: List[str],
    ) -> str:
        """Sends a message, including media, within an existing chat session."""
        prompt_parts: List[Any] = [query_prompt]
        error_messages: List[str] = []

        for path_or_url in media_paths:
            try:
                file_to_process = await self._prepare_media_file(path_or_url)
                if file_to_process:
                    print(f"Uploading file for chat: {file_to_process.name}")
                    uploaded_file = genai.upload_file(path=file_to_process)
                    prompt_parts.append(uploaded_file)
                else:
                    error_messages.append(f"Failed to process media path: {path_or_url}")
            except Exception as e:
                message = f"Error processing '{path_or_url}' for chat: {e}"
                print(message)
                error_messages.append(message)

        model_response_text = ""
        if len(prompt_parts) > 0:
            print("\nSending message to Gemini chat...")
            response = await chat.send_message_async(
                prompt_parts,
                request_options={"timeout": 300.0},
            )
            model_response_text = response.text
        else:
            model_response_text = "Warning: No valid prompt or media to send."

        if error_messages:
            error_summary = "\n\n--- Issues During Processing ---\n" + "\n".join(error_messages)
            return model_response_text + error_summary

        return model_response_text

    async def _prepare_media_file(self, path_or_url: str) -> Optional[Path]:
        """Handles URL downloading or validates local file paths."""
        path_or_url = path_or_url.strip()
        is_url = path_or_url.startswith(("http://", "https://"))

        if is_url:
            downloaded_path = await UrlDownloaderTool().download_file_from_url(url=path_or_url)
            if downloaded_path:
                self.temp_files_to_clean.append(downloaded_path)
                return downloaded_path
            return None
        else:
            local_path = Path(path_or_url).resolve()
            if local_path.exists():
                return local_path
            print(f"Skipping non-existent local file: {path_or_url}")
            return None

    def cleanup_temp_files(self):
        """Cleans up any temporary files created during the session."""
        print("Cleaning up temporary files...")
        for f in self.temp_files_to_clean:
            try:
                os.remove(f)
                print(f"Cleaned up temporary file: {f}")
            except OSError as e:
                print(f"Error cleaning up temporary file {f}: {e}")
