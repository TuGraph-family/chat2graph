import base64
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import uuid

from mcp.types import EmbeddedResource, ImageContent, TextContent

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
        task_context: Optional[str] = None,
    ) -> str:
        """Analyzes the current webpage to determine the single best next step towards your goal.

        This is a powerful visual analysis tool. In a multi-step task, you should call this tool
        repeatedly after each action (like a click or type) to re-evaluate the new page state.

        **When to use this tool:**
        Use this tool as your primary 'eyes' to understand a webpage. Call it after navigating to a
        new page, or after performing an action that changes the page content.

        **Strategy for Multi-Step Tasks:**
        This tool supports conversational context to become more efficient and accurate over time.
        - **First Call:** On a new page, use ONLY the `vlm_task` parameter to describe the overall goal.
        - **Subsequent Calls:** After performing an action (e.g., dismissing a pop-up, clicking 'next page'),
          call this tool again. This time, provide BOTH:
            1. `vlm_task`: The SAME overall goal, including the conditions or the constraints something else.
            2. `task_context`: A brief summary of the last action and the current situation.
          This helps the VLM understand the progress and not get confused.

        **How to formulate `vlm_task` and `task_context`:**

        *   **`vlm_task` (The Unchanging Goal):**
            - "Find and book the cheapest flight from JFK to LAX for tomorrow."
            - "Summarize the return policy of this product."
            - "Find the number of publications by author X published before 2020."
            - "I have now used Google to search for a certain keyword. Please tell me what the search results are and what the index of the element I need to interact with next is?"

        *   **`task_context` (The Evolving Situation):**
            - *After dismissing a cookie banner:* "I have just dismissed the cookie banner. Now I need to see the main content."
            - *After clicking 'next page':* "I am now on page 2 of the search results. I need to continue my search here."
            - *In your ORCID example:* "I am on the second page of the author's works. I already counted 28 pre-2020 publications on the first page. Now I need to count the ones on this page."

        **How to Use the Output (Your Action Plan):**

        1.  **If `result_type` is `ANSWER`:**
            - The task is done. The final answer is in `data.answer`.

        2.  **If `result_type` is `INTERACT`:**
            - You need to perform a UI action.
            - The action details are in `data.interaction_recommendation` (contains `element_index`, `value`).
            - **After performing the action**, you MUST call this tool again with an updated `task_context` to analyze the new page state.
            - **If `information_status` is `PARTIAL`**, you've found partial data in `data.partial_answer`. Save it before you continue.

        3.  **If `result_type` is `NAVIGATE_OR_SEARCH`:**
            - The current page cannot fulfill the goal.
            - You need to perform a different action, like using a search tool or navigating to a new URL. The reason is in `data.answer`.

        4.  **If `result_type` is `CLARIFY`:**
            - The goal is too vague.
            - You need to ask the me for more details. The question to ask is in `data.answer`.

        Returns:
            A JSON object with a clear recommendation for the next step. Your can check the `status` and `result_type` fields to decide your next action.
            **Example 1: A Final Answer is Found**
            ```json
            {
                "status": "COMPLETED",
                "result_type": "ANSWER",
                "data": { "answer": "The author published 65 articles before 2020." }
            }
            ```

            **Example 2: An Interaction is Needed (with partial info)**
            ```json
            {
                "status": "ACTION_NEEDED",
                "result_type": "INTERACT",
                "information_status": "PARTIAL",
                "data": {
                    "interaction_recommendation": { "element_index": 52, "value": "" },
                    "partial_answer": "Found 28 articles on page 1."
                }
            }
            ```
        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "vlm_task": {
                    "type": "string",
                    "description": "Describe what you ultimately want to achieve on this website."
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

        multi_modal_tool = GeminiMultiModalTool()

        # get both clean and highlighted screenshots ===
        clean_results = await mcp_connection.call(
            tool_name="browser_read_and_get_state",
            include_screenshot=True,
            screenshot_with_highlighted_elements=False,
        )
        _, clean_screenshot_base64 = self._parse_mcp_results(clean_results)
        clean_screenshot_path = self._save_screenshot(clean_screenshot_base64, temp_dir, "clean")

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

        # LLM call with both screenshots
        analysis_prompt = self._get_analysis_prompt(vlm_task, task_context, highlighted_page_state)
        vlm_result_str = await multi_modal_tool.call_multi_modal(
            query_prompt=analysis_prompt,
            media_paths=[clean_screenshot_path, highlighted_screenshot_path],
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
    ) -> Tuple[Dict[str, Any], str]:
        """Parses MCP results to extract page state and screenshot."""
        if not results or not isinstance(results[0], TextContent):
            raise ValueError("Expected a text content block with page state info.")
        page_state = json.loads(results[0].text)
        screenshot_base64 = page_state.get("screenshot")
        if not screenshot_base64:
            raise ValueError(
                "Screenshot not found in the page state, "
                f"and the keys of page state are: {list(page_state.keys())}"
            )
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
        task_context: Optional[str] = None,
        page_state: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates a unified prompt for analyzing both clean and highlighted screenshots."""

        base_prompt = f'''As an expert web agent, analyze the provided webpage screenshots to determine the single best next step towards my goal.

I'm providing you with TWO screenshots of the same webpage:
1. **FIRST IMAGE (Clean)**: The webpage without any highlighting - use this for content analysis.
2. **SECOND IMAGE (Highlighted)**: The same webpage with interactive elements marked with numbered boxes - use this for element indices identification. All interactive elements are marked with a rectangular box and a number in the top left corner of the box. Therefore, you can visually identify which element(s) we need to interact with. Special case: sometimes many labels may cluster together, or some boxes may be misaligned, so for uncertain indices, use your best judgment.


My ultimate goal: "{vlm_task}"'''  # noqa: E501

        if task_context:
            base_prompt += f'''
**Current Task Context:** You are not starting from scratch. Here is what has happened so far:
"{task_context}"'''

        page_state_without_screenshot = page_state.copy() if page_state else {}
        page_state_without_screenshot.pop("screenshot", None)

        base_prompt += f"""
**Page State Data:**
{json.dumps(page_state_without_screenshot, indent=2) if page_state_without_screenshot else "No additional page data available"}



**Your Analysis Process:**

Please analyze the situation and give me your recommendation. Follow this thinking process carefully:**

**Step 1: Strategic Analysis (using the FIRST/Clean image)**
*   First and foremost, look for any **blocking elements** like cookie banners, login popups, or newsletter sign-ups. Is there anything preventing me from seeing or interacting with the main content? If so, dealing with that is our absolute top priority.
*   Next, understand the page's purpose and content in relation to my goal. Can my goal be achieved on this page?
*   Based on this, determine which of the following four scenarios we are in.

**Step 2: Tactical Recommendation (using BOTH images as needed)**
*   Now, formulate your response to me based on the scenario you identified. Speak directly to me.

---
**Please structure your response based on ONE of these four scenarios:**

**Scenario 1: You found the final answer directly.**
If you can fully answer my `vlm_task` just by looking at the clean screenshot, tell me the answer directly. You don't need to recommend any action or mention any element indices.
*   **Example Response:** "I've found the answer for you. The contact email is support@example.com."

**Scenario 2: You need me to perform an action to achieve the goal.**
This applies if the page is ready for interaction (e.g., a search form) or if a blocker needs to be dismissed.
*   Tell me what action I need to take (e.g., "You should click the 'Login' button," or "You need to accept the cookies first.").
*   Then, look at the **SECOND/Highlighted image** to find the exact `element_index` for the target element.
*   If you're certain, provide it like this: `element_index: 42`.
*   If the element is an input field, also tell me what to type: `value: "laptops"`.
*   If you're unsure about the index because of crowding or misalignment, give me your best guess and list other possibilities: `element_index: 42`, `ambiguous_element_indices: [43, 102]`. Also, briefly explain your reasoning for the uncertainty.
*   **Example Response:** "To proceed, you need to log in. I see a 'Login' button. Looking at the highlighted image, the correct element seems to be `element_index: 15`. There's another similar button at index 16, but index 15 is more prominent."

**Scenario 3: You found a partial answer, but more action is needed.**
This is for situations like paginated results or "read more" sections.
*   First, give me the partial information you found.
*   Then, recommend the next action I need to take to get the rest of the information, following the same format as Scenario 2 (providing `element_index`, etc.).
*   **Example Response:** "I've found 10 search results on this page that match your criteria. However, it says 'Page 1 of 5', so there's more to see. You should click the 'Next Page' button. From the highlighted image, that's `element_index: 88`."

**Scenario 4: My goal cannot be achieved here.**
If the current page is completely irrelevant to my goal (e.g., I'm on Google but my goal is to 'check my shopping cart').
*   Explain to me why we can't proceed here and suggest what I should do instead (e.g., navigate to a different URL, use a search tool).
*   **Example Response:** "It looks like we're on a news article page, but your goal is to check your email. We can't do that from here. You should probably navigate to your email provider's website first."

**Please begin your analysis now.**"""  # noqa: E501

        return base_prompt
