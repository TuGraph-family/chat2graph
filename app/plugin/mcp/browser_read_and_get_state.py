import base64
import json
import os
from typing import Any, Dict, List, Optional, Union
import uuid

from mcp.types import EmbeddedResource, ImageContent, TextContent

from app.core.model.task import ToolCallContext
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.mcp.mcp_service import McpService
from app.core.toolkit.system_tool.gemini_multi_modal_tool import GeminiMultiModalTool
from app.core.toolkit.tool import Tool


class BrowserReadAndGetStateTool(Tool):
    """
    A tool to read the current state of a webpage, including interactive elements,
    and optionally perform a Visual Question Answering (VQA) task on a screenshot of the page.
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
        use_vlm: bool = True,
        vlm_task: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reads the interactive elements from the current webpage and optionally uses a VLM to analyze a screenshot and recommend a next step.

        **When to use this tool:**
        Use this tool to get a comprehensive understanding of the current page's state.
        It's particularly useful for visually analyzing the page to understand its layout, identify interactive elements, and get a recommendation for the next step to achieve a larger goal.

        **How to formulate an effective `vlm_task`:**
        The `vlm_task` should describe what the user wants to ultimately achieve. The VLM will observe the screen and recommend the best immediate next step towards that goal.

        *   **For clicking an element:** "I want to log in." The VLM will see a 'Login' button and recommend an 'INTERACT' action with the element's index.
        *   **For filling an input field:** "I want to search for 'laptops'." The VLM will find the search bar and recommend an 'INTERACT' action with the input's index and the value 'laptops'.
        *   **For answering a question about the page:** "What is the price of the 'Pro Plan'?" The VLM will find the answer on the screen and recommend an 'ANSWER' action with the answer.
        *   **For scrolling:** "I need to find the contact information." The VLM might see that the information is not on the screen and recommend a 'SCROLL' action.

        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "use_vlm": {
                    "type": "bool",
                    "description": "Whether to use the VLM to analyze the screenshot and recommend a next step. Defaults to True."
                },
                "vlm_task": {
                    "type": "string",
                    "description": "A prompt that describes the user's ultimate goal. The VLM will analyze the screenshot and this goal to recommend a single, immediate next step. The more context you provide in the question, the better the VLM can understand the task. Required if use_vlm is True."
                },
            },
            "required": []
        }
        """  # noqa: E501
        # Get the MCP connection
        toolkit_service: ToolkitService = ToolkitService.instance
        mcp_service: Optional[McpService] = None
        toolkit = toolkit_service.get_toolkit()
        for item_id in toolkit.vertices():
            tool_group = toolkit.get_tool_group(item_id)
            if tool_group and isinstance(tool_group, McpService):
                if tool_group._tool_group_config.name == "BrowserTool":
                    mcp_service = tool_group
                    break
        if not mcp_service:
            raise ValueError("MCP service (BrowserTool) not registered in the toolkit.")

        mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)

        # get interactive elements and screenshot
        interactive_elements_results: List[
            Union[TextContent, ImageContent, EmbeddedResource]
        ] = await mcp_connection.call(
            tool_name="browser_read_and_get_state", include_screenshot=use_vlm
        )
        assert interactive_elements_results and isinstance(
            interactive_elements_results[0], TextContent
        ), "Expected a text content block with the interactive elements info."
        interactive_elements_json = interactive_elements_results[0].text

        page_state: Dict[str, Any] = json.loads(interactive_elements_json)

        if use_vlm:
            if not vlm_task:
                raise ValueError("vlm_task is required when use_vlm is True.")

            screenshot_base64 = page_state.get("screenshot")
            if not screenshot_base64:
                raise ValueError(
                    "Screenshot not found in the result of browser_read_and_get_state."
                )

            # save screenshot to a temporary file
            temp_dir = "./.gaia_tmp/"
            os.makedirs(temp_dir, exist_ok=True)
            screenshot_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")
            page_state["screenshot"] = screenshot_path
            print(f"Screenshot saved to {screenshot_path}")

            image_data = base64.b64decode(screenshot_base64)
            with open(screenshot_path, "wb") as f:
                f.write(image_data)

            # call VLM
            structured_prompt = self._get_visual_query_prompt(vlm_task, page_state)
            vlm_result_str = await GeminiMultiModalTool().call_multi_modal(
                query_prompt=structured_prompt, media_paths=[screenshot_path]
            )
            page_state["vlm_result"] = vlm_result_str

        return page_state

    def _get_visual_query_prompt(self, question: str, elements: Dict[str, Any]) -> str:
        elements_str = json.dumps(elements, indent=2)
        prompt = f'''You are an AI assistant that analyzes a webpage to recommend the next action toward a user's goal.
The user's goal is: "{question}"

You are given two things:
1.  A screenshot of the **entire webpage**. On this screenshot, there are numbered boxes drawn around the interactive elements that are **currently visible in the browser's viewport**.
2.  A JSON list of these currently visible interactive elements. The `index` in the JSON corresponds to the number in the box on the screenshot.

Your task is to analyze the user's goal, the full-page screenshot, and the labeled elements to recommend ONE single, immediate next step.

JSON list of currently visible interactive elements:
{elements_str}

Recommend one of the following actions:
1.  **INTERACT**: To click or type into a visible, numbered element. Use this if the target element is clearly visible and labeled in the current viewport.
2.  **SCROLL**: To scroll the page down or up. You can specify the number of times to scroll. Use this if the target element is not in the current labeled view, but you can see it elsewhere in the full-page screenshot or have reason to believe it exists on the page.
3.  **ANSWER**: To directly answer the user's question if the information is visible and labeled in the current viewport.

Your output MUST be a single JSON object matching this exact schema:
{{
    "thinking": "Your step-by-step reasoning. First, what is the user's goal? Second, I will check if the target element or information is in the current list of labeled interactive elements. If yes, I will recommend 'INTERACT' or 'ANSWER'. If no, I will analyze the entire screenshot to see if the element exists outside the labeled area. If it seems likely the element is further down or up, my primary recommendation is to 'SCROLL'. I can also decide how many times to scroll based on how far away the target seems. I can suggest to interact with non-target elements (like cookie banners) if they are preventing any browser action, including scrolling.",
    "recommendation": {{
        "type": "INTERACT | SCROLL | ANSWER",
        "element_index": "Integer index of the element to interact with. (Required for INTERACT)",
        "value": "String value to type into an input field. (Optional for INTERACT)",
        "scroll_direction": "UP | DOWN. (Required for SCROLL)",
        "times": "Integer, number of times to scroll. Defaults to 1. (Optional for SCROLL)",
        "answer": "The direct answer to the user's question. (Required for ANSWER)"
    }}
}}

**IMPORTANT**: Do not assume an action is impossible just because the element is not currently labeled. It may be visible elsewhere on the full-page screenshot. Prioritize scrolling if the target is not in the labeled view.

'''  # noqa: E501
        return prompt
