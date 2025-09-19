import base64
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from litellm import completion
from litellm.litellm_core_utils.streaming_handler import CustomStreamWrapper
from litellm.types.utils import ModelResponse
from mcp.types import EmbeddedResource, ImageContent, TextContent

from app.core.common.system_env import SystemEnv
from app.core.model.task import ToolCallContext
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.mcp.mcp_service import McpService
from app.core.toolkit.system_tool.gemini_multi_modal_tool import GeminiMultiModalTool
from app.core.toolkit.tool import Tool


class BrowserReadAndGetStateTool(Tool):
    """An intelligent tool that analyzes a webpage using a conversational VLM to
    determine the single best next step towards a goal. It can answer
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
        vlm_task_context: str,
        agent_full_context: str,
    ) -> str:
        """Analyzes the current webpage to determine the single best next step towards your goal by inheriting the main Agent's full context.

        This is a powerful visual analysis tool. In a multi-step task, you should call this tool
        repeatedly after each action (like a click or type) to re-evaluate the new page state.

        **When to use this tool:**
        Use this tool as your primary 'eyes' to understand a webpage. It acts as an extension of your own reasoning, equipped with your full operational context.

        **How to formulate parameters:**

        *   **`vlm_task` (The Unchanging Goal):**
            - "Find and book the cheapest flight from JFK to LAX for tomorrow."
            - "Summarize the return policy of this product."

        *   **`vlm_task_context` (The Evolving Situation):**
            - *Initial state:* "I have just navigated to the page to begin the task."
            - *After an action:* "I have just dismissed the cookie banner. Now I need to see the main content."

        *   **`agent_full_context` (Your Entire Mind):**
            - This is the most critical parameter. You must pass your **complete System Prompt and the full conversation history** here. This ensures the visual analysis module operates with the exact same rules, principles, and memory that you do.

        Returns:
            str: returns a natural language (or semi-structured) string, analyzed with the full agent context, describing the next best step or final answer based on the visual information. The output format will follow the familiar 4-scenario structure:
                Scene 1 - Final answer:
                    Indicates that the result has been obtained directly, usually in a format like:
                    "Completed: The author published a total of 70 articles before 1999."
                    or
                    "Answer found: The contact email is support@example.com."
                Scene 2 - Requires interactive action:
                    Describes the single action to be performed next and provides (if determinable) element index; may include input values; if uncertain, candidates will be given. For example:
                    "Please click the login button, element_index: 15."
                    "It is necessary to close the pop-up window, possible elements: element_index: 42 (not very sure, candidates: 43, 57)."
                    "Please enter 'laptops' in the search box and submit, element_index: 12, value: laptops."
                Scene 3 - Partial information + next action:
                    First summarizes the partial information obtained and then gives the next interaction. For example:
                    "A total of 28 results meeting criteria have been counted on page one. Please click next page, element_index: 88."
                    or
                    "I have seen 10 results; the page shows Page 1 /5; continue clicking Next, element_index:34."
                Scene 4 - Current page not suitable for achieving goal:
                    Explains why and suggests a new direction. For example:
                    "The current page is a news article; it cannot continue executing 'view shopping cart' goal; it is recommended to navigate to the mall homepage first."
                Possible additional elements (optional, depending on circumstances):
                    - partial_answer: (if for Scene 3)
                    - ambiguous_element_indices: A list of candidate indices provided when there are uncertainties.
                    - reasoning: A brief explanation of uncertainty or basis for judgment.


        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "vlm_task": {
                    "type": "string",
                    "description": "Describe what you ultimately want to achieve on this website. This is the overall mission."
                },
                "vlm_task_context": {
                    "type": "string",
                    "description": "A summary of what has already been accomplished or the current state of the multi-step task. This is the immediate situation."
                },
                "agent_full_context": {
                    "type": "string",
                    "description": "CRITICAL: The main agent's full context, including its System Prompt and the entire conversation history. This allows the visual model to adopt the agent's persona and reasoning."
                }
            },
            "required": ["vlm_task", "vlm_task_context", "agent_full_context"]
        }
        """  # noqa: E501
        mcp_service = self._get_mcp_service()
        mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)
        temp_dir = "./.gaia_tmp/"
        os.makedirs(temp_dir, exist_ok=True)

        # get both clean and highlighted screenshots
        clean_results = await mcp_connection.call(
            tool_name="browser_read_and_get_state",
            include_screenshot=True,
            screenshot_with_highlighted_elements=False,
        )
        highlighted_results = await mcp_connection.call(
            tool_name="browser_read_and_get_state",
            include_screenshot=True,
            screenshot_with_highlighted_elements=True,
        )

        _, clean_screenshot_base64 = self._parse_mcp_results(clean_results)
        highlighted_page_state, highlighted_screenshot_base64 = self._parse_mcp_results(
            highlighted_results
        )
        image_base64s: List[str] = []
        image_paths: List[str] = []
        screenshot_context: Optional[str] = None
        if clean_screenshot_base64 and not highlighted_screenshot_base64:
            image_paths.append(self._save_screenshot(clean_screenshot_base64, temp_dir, "clean"))
            image_base64s = [clean_screenshot_base64]
            screenshot_context = (
                "\nSystem unexpected situation: Only the clean screenshot could be "
                "captured from the current page. The current page might be a PDF, embedded media, "
                "pages with special rendering or other non-standard web page. "
                "You can download the page instead."
            )
            print(f"Warning: {screenshot_context}")
        elif not clean_screenshot_base64 and highlighted_screenshot_base64:
            image_paths.append(
                self._save_screenshot(highlighted_screenshot_base64, temp_dir, "highlighted")
            )
            image_base64s = [highlighted_screenshot_base64]
            screenshot_context = (
                "\nSystem unexpected situation: Only the highlighted screenshot "
                "could be captured from the current page. The current page might be a PDF, "
                "embedded media, pages with special rendering or other non-standard web page. "
                "You can download the page instead."
            )
            print(f"Warning: {screenshot_context}")
        elif clean_screenshot_base64 and highlighted_screenshot_base64:
            image_paths.append(self._save_screenshot(clean_screenshot_base64, temp_dir, "clean"))
            image_paths.append(
                self._save_screenshot(highlighted_screenshot_base64, temp_dir, "highlighted")
            )
            image_base64s = [clean_screenshot_base64, highlighted_screenshot_base64]
        else:
            image_base64s = []
            screenshot_context = (
                "\nSystem unexpected situation: No screenshots could be captured from "
                "the current page. The current page might be a PDF, embedded media, pages with "
                "special rendering or other non-standard web page. "
                "You can download the page instead."
            )
            print(f"Error: {screenshot_context}")
            raise ValueError(f"Error: {screenshot_context}")

        # LLM call with both screenshots using OpenRouter API (with Gemini fallback)
        analysis_prompt = self._get_analysis_prompt(
            vlm_task,
            vlm_task_context,
            agent_full_context,
            screenshot_context,
            highlighted_page_state,
        )
        vlm_result_str = await self._call_multimodal_model(
            query_prompt=analysis_prompt,
            image_base64s=image_base64s,
            temp_dir=temp_dir,
        )

        return vlm_result_str

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
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """Parses MCP results to extract page state and screenshot."""
        if not results or not isinstance(results[0], TextContent):
            raise ValueError("Expected a text content block with page state info.")
        try:
            page_state = json.loads(results[0].text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse page state JSON: {e}\nContent: {results[0].text}"
            ) from e
        screenshot_base64: Optional[str] = page_state.get("screenshot", None)
        return page_state, screenshot_base64

    def _save_screenshot(self, b64_string: str, directory: str, prefix: str) -> str:
        """Saves a base64-encoded screenshot to a file."""
        path = os.path.join(directory, f"{prefix}_{uuid.uuid4()}.png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64_string))
        print(f"Screenshot saved to {path}")
        return path

    def _get_analysis_prompt(
        self,
        vlm_task: str,
        vlm_task_context: str,
        agent_full_context: str,
        screenshot_context: Optional[str] = None,
        page_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates a unified prompt for analyzing both clean and highlighted screenshots."""
        agent_context_prompt = f"""
---
**OVERARCHING DIRECTIVES & CONTEXT FROM THE PRIMARY AGENT**
Before analyzing the webpage, you must first internalize the following context. This information contains the primary agent's core principles, rules, and conversation history. Your entire analysis and all recommendations MUST be fully compliant with these directives. This is your foundational knowledge.

{agent_full_context}
---

With the above context fully understood, you will now perform a specific visual analysis task. All the instructions below must be interpreted through the lens of the primary agent's directives you have just read.
"""  # noqa: E501

        base_prompt = f'''As an expert web agent, your task is to analyze the provided webpage information to determine the single best next step to achieve my goal.

    You are provided with three sources of information:
    1.  **FIRST IMAGE (Clean Screenshot)**: The webpage without any highlighting. Use this for overall layout, context, and content analysis.
    2.  **SECOND IMAGE (Highlighted Screenshot)**: The same webpage where interactive elements are marked with numbered boxes. Use this for visual confirmation and disambiguation of elements.
    3.  **Webpage Data (JSON)**: Structured data about the page, including the URL, title, and a detailed list of all `interactive_elements`. This is your primary source for finding the precise `element_index` and verifying element properties like text or links.

My ultimate goal: "{vlm_task}"'''  # noqa: E501

        base_prompt += f'''
**Current Task Context:** You are not starting from scratch. Here is what has happened so far:
"{vlm_task_context}"'''
        if screenshot_context:
            base_prompt += f"""
**Screenshot Context Note:** {screenshot_context}"""
        page_state_without_screenshot = page_state.copy() if page_state else {}
        page_state_without_screenshot.pop("screenshot", None)

        base_prompt += f"""
**Webpage Data:**
{json.dumps(page_state_without_screenshot, indent=2) if page_state_without_screenshot else "No additional page data available"}



**Your Analysis Process:**

Please follow this thinking process carefully to formulate your recommendation:

**Step 1: Strategic Analysis (using the FIRST/Clean image)**
*   First and foremost, look for any **blocking elements** like cookie banners, login popups, or newsletter sign-ups. Is there anything preventing me from seeing or interacting with the main content? If so, dealing with that is our absolute top priority.
*   Next, understand the page's purpose and content in relation to my goal. Can my goal be achieved on this page?
    *   Sometimes, when we are using search engines (e.g. Google), we may see AI Overviews from the search engine, which are summaries of the content of some queried web pages related to the search query. However, the answers to the query provided by AI Overviews may be inaccurate or misleading. Therefore, for greater accuracy, I hope you can recommend that I click on a specific webpage index rather than just providing the content of the AI Overviews.
*   Based on this, determine which of the following four scenarios we are in.
**Step 2: Tactical Recommendation (using BOTH images as needed)**
*   Now, formulate your response to me based on the scenario you identified.

---
**Please structure your response based on ONE of these four scenarios:**

**Scenario 1: You found the final answer directly.**
If you can fully answer my `vlm_task` just by looking at the clean screenshot, tell me the answer directly. You don't need to recommend any action or mention any element indices.
*   **Example Response:** "I've found the answer for you. The contact email is support@example.com."

**Scenario 2: You need me to perform an action to achieve the goal.**
This applies if the page is ready for interaction (e.g., a search form) or if a blocker needs to be dismissed.
*   Tell me what action I need to take (e.g., "You should click the 'Login' button," or "You need to accept the cookies first.").
*   Then, look at the **SECOND/Highlighted image** to find the exact `element_index` with related details for the target element.
*   If you're certain, provide it like this: `element_index: 42 (tag: ..., text: ..., href: ..., placeholder: ...)`.
*   If the element is an input field, also tell me what to type: `value: "laptops"`.
*   If you're unsure about the index because of crowding or misalignment, give me your best guess and list other possibilities: `element_index: 42 (tag: ..., text: ..., href: ..., placeholder: ...)`, `ambiguous_element_indices: [43 (tag: ..., text: ..., href: ..., placeholder: ...), 102 (tag: ..., text: ..., href: ..., placeholder: ...)]`. Also, briefly explain your reasoning for the uncertainty.
*   **Example Response:** "To proceed, you need to log in. I see a 'Login' button. Looking at the highlighted image, the correct element seems to be `element_index: 15 (tag: 'a', text: 'Log in', href: 'https://...', placeholder: None)`. There's another similar button at index 16(...), but index 15 is more prominent."

**Scenario 3: You found a partial answer, but more action is needed.**
This is for situations like paginated results or "read more" sections.
*   First, give me the partial information you found.
*   Then, recommend the next action I need to take to get the rest of the information, following the same format as Scenario 2 (providing `element_index`, etc.). And waht is more, if you are asked to find information that info resource/page is likely to be a PDF reader, please recommend me to download the PDF to let me read it locally.
*   **Example Response:** "I've found 10 search results on this page that match your criteria. However, it says 'Page 1 of 5', so there's more to see. You should click the 'Next Page' button. From the highlighted image, that's `element_index: 88 (tag: ..., text: ..., href: ..., placeholder: ...)`."

**Scenario 4: My goal cannot be achieved here.**
If the current page is completely irrelevant to my goal (e.g., I'm on Google but my goal is to 'check my shopping cart').
*   Explain to me why we can't proceed here and suggest what I should do instead (e.g., navigate to a different URL, use a search tool).
*   **Example Response:** "It looks like we're on a news article page, but your goal is to check your email. We can't do that from here. You should probably navigate to your email provider's website first."

**Please begin your analysis now.**"""  # noqa: E501

        return agent_context_prompt + base_prompt

    async def _call_gemini_multimodal_model(self, query_prompt: str, image_paths: List[str]) -> str:
        """Call Gemini first for multimodal analysis"""
        gemini_tool = GeminiMultiModalTool()
        return await gemini_tool.call_multi_modal(
            query_prompt=query_prompt,
            media_paths=image_paths,
        )

    async def _call_multimodal_model(
        self, query_prompt: str, image_base64s: List[str], temp_dir: str
    ) -> str:
        """Call OpenRouter first for multimodal analysis; fallback to Gemini if OpenRouter fails."""
        # build message content for OpenRouter
        content: List[Dict[str, Any]] = [{"type": "text", "text": query_prompt}]
        for image_base64 in image_base64s:
            data_url = f"data:image/png;base64,{image_base64}"
            content.append({"type": "image_url", "image_url": {"url": data_url}})
        messages = [{"role": "user", "content": content}]

        # Primary: OpenRouter
        try:
            response: Union[ModelResponse, CustomStreamWrapper] = completion(
                model=SystemEnv.BROWSER_LLM_NAME,
                api_base=SystemEnv.BROWSER_LLM_ENDPOINT,
                api_key=SystemEnv.BROWSER_LLM_APIKEY,
                messages=messages,
                temperature=SystemEnv.TEMPERATURE,
                stream=False,
                timeout=60,
                max_retries=2,
            )
            assert isinstance(response, ModelResponse)
            # Check for error messages in response content
            response_content = response["choices"][0]["message"]["content"]
            if "error" in response_content.lower() and (
                "service unavailable" in response_content.lower()
                or "rate limit" in response_content.lower()
            ):
                raise ValueError(f"OpenRouter service error: {response_content}")
            return response_content
        except Exception as openrouter_error:
            print(f"OpenRouter primary failed: {openrouter_error}")
            print("Falling back to Gemini multimodal model...")
            # Fallback: Gemini
            try:
                temp_image_paths = []
                for i, image_base64 in enumerate(image_base64s):
                    image_type = "clean" if i == 0 else "highlighted"
                    temp_path = self._save_screenshot(
                        image_base64, temp_dir, f"gemini_{image_type}"
                    )
                    temp_image_paths.append(temp_path)
                gemini_tool = GeminiMultiModalTool()
                gemini_result = await gemini_tool.call_multi_modal(
                    query_prompt=query_prompt,
                    media_paths=temp_image_paths,
                )
                if (
                    "quota" in gemini_result.lower()
                    or "temporarily unavailable" in gemini_result.lower()
                ):
                    raise ValueError("Gemini service quota exceeded or temporarily unavailable.")
                return gemini_result
            except Exception as gemini_error:
                print(f"Gemini fallback also failed: {gemini_error}")
                return (
                    "Error: Both OpenRouter (primary) and Gemini (fallback) visual analysis "
                    "services failed. "
                    f"OpenRouter error: {openrouter_error}. "
                    f"Gemini error: {gemini_error}. "
                    "Please try again later. You can still use other browser tools like "
                    "navigation, clicking, or typing if you know what actions to take."
                )
