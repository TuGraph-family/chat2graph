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
        vlm_task: str,
        return_interactive_elements: bool = False,
    ) -> Dict[str, Any]:
        """Reads the interactive elements from the current webpage, uses a VLM to analyze a screenshot, and recommends a next step. It returns the VLM's analysis result and the path to the screenshot.

        **When to use this tool:**
        Use this tool to get a comprehensive understanding of the current page's state.
        It's particularly useful for visually analyzing the page to understand its layout, identify interactive elements, and get a recommendation for the next step to achieve a larger goal.

        **How to formulate an effective `vlm_task`:**
        The `vlm_task` should describe what the user wants to ultimately achieve. The VLM will observe the screen and recommend the best immediate next step towards that goal.

        *   **For clicking an element:** "I want to log in." The VLM will see a 'Login' button and recommend an 'INTERACT' action with the element's index.
        *   **For filling an input field:** "I want to search for 'laptops'." The VLM will find the search bar and recommend an 'INTERACT' action with the input's index and the value 'laptops'.
        *   **For answering a question about the page:** "What is the price of the 'Pro Plan'?" The VLM will find the answer on the screen and recommend an 'ANSWER' action with the answer.

        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "vlm_task": {
                    "type": "string",
                    "description": "A prompt that describes the user's ultimate goal. The VLM will analyze the screenshot and this goal to recommend a single, immediate next step. The more context you provide in the question, the better the VLM can understand the task."
                },
                "return_interactive_elements": {
                    "type": "boolean",
                    "description": "If true, the result will include the JSON of interactive elements of the current web page, which helps you to interact with the page more effectively. This JSON may be very redundant and contain sometimes more than 300 elements info. It is recommended to use the default settings (False).",
                    "default": false
                }
            },
            "required": ["vlm_task"]
        }
        """  # noqa: E501
        return_interactive_elements = False

        # get the MCP connection
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
            tool_name="browser_read_and_get_state",
            include_screenshot=True,
        )
        assert interactive_elements_results and isinstance(
            interactive_elements_results[0], TextContent
        ), "Expected a text content block with the interactive elements info."
        interactive_elements_json = interactive_elements_results[0].text

        try:
            page_state: Dict[str, Any] = json.loads(interactive_elements_json)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to get the browser state. Received: {interactive_elements_json}"
            ) from e

        screenshot_base64s: Optional[str] = page_state.get("screenshot")
        if not screenshot_base64s:
            raise ValueError(
                "Screenshot has not been captured, so that the tool can not view the web page."
            )

        # save screenshot to a temporary file
        temp_dir = "./.gaia_tmp/"
        os.makedirs(temp_dir, exist_ok=True)
        b64_tile_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")
        page_state["screenshot"] = [b64_tile_path]
        print(f"Screenshot saved to {b64_tile_path}")

        image_data = base64.b64decode(screenshot_base64s)
        with open(b64_tile_path, "wb") as f:
            f.write(image_data)

        # call VLM
        structured_prompt = self._get_visual_query_prompt(
            vlm_task,
            page_state["screenshot"],
            page_state,
        )
        vlm_result_str = await GeminiMultiModalTool().call_multi_modal(
            query_prompt=structured_prompt, media_paths=page_state["screenshot"]
        )
        page_state["vlm_result"] = vlm_result_str

        if return_interactive_elements:
            return page_state

        return {"vlm_result": page_state["vlm_result"], "screenshot": page_state["screenshot"]}

    def _get_visual_query_prompt(
        self, question: str, media_paths: List[str], elements: Dict[str, Any]
    ) -> str:
        elements_str = json.dumps(elements, indent=2)
        prompt = f'''You are an AI assistant that analyzes a webpage to recommend the next action toward a user's goal.
The user's goal is: "{question}"

You are given two things:
1.  A/Some screenshot(s) of the **entire webpage**. On this screenshot, there are numbered boxes drawn around the interactive elements that are **currently visible in the browser's viewport**.
2.  A JSON list of these currently visible interactive elements. The `index` in the JSON corresponds to the number in the box on the screenshot.

Given screenshots:
{media_paths}

Your task is to analyze the user's goal, the full-page screenshot, and the labeled elements to recommend ONE single, immediate next step.

**Attention**: If the screenshot shows a document reader (such as PDF), and you find that the view in the screenshot is limited, and you think the document on this webpage is downloadable, you can suggest that the next step is to click the download button or download the document via URL.

**Attention**: Information may not be fully presented on a single static page. You must proactively identify scenarios where interaction is necessary to obtain answers. This requires you to understand the page layout and anticipate where information might be hidden, just like a human user would.
    - For example: When a long article or search results are displayed in pages, you need to navigate by clicking "Next" or the page numbers; when key information is hidden in collapsible "Show More" or "Details" sections, you need to perform clicks to expand the content; when an answer requires jumping from one link to another page, you must track that link. Ignoring these interaction needs will result in incomplete information retrieval.

**Attention**: If the screenshot is about search engine summaries, especially **AI Overview** (or **AI Some Thing**), you can select information from the so-called AI content, but you must indicate that this is content from an AI overview and inform me that your information is not reliable. Then please provide the next page to facilitate my access to specific credible websites through the search engine for my next steps.

JSON list of currently visible interactive elements:
{elements_str}

Recommend one of the following actions:
1.  **INTERACT**: To click or type into a numbered element. Use this if the target element is clearly visible and labeled in the current viewport.
2.  **ANSWER**: To directly answer the user's question if the information is visible and labeled in the current viewport.

Your output MUST be a single JSON object matching this exact schema:

{{
    "description": "A description of the view of the webpage, since you are the only one who can see it.",
    "thinking": "Your step-by-step reasoning. First, what is the user's goal? Second, I will check if the target element or information is in the current list of labeled interactive elements. If yes, I will recommend 'INTERACT' or 'ANSWER', if not, explain it. I can suggest to interact with non-target elements (like cookie banners) if they are preventing any browser action.",
    "recommendation": {{
        "type": "INTERACT | ANSWER",
        "element_index": "Integer index of the element to interact with. (Required for INTERACT)",
        "value": "String value to type into an input field. (Optional for INTERACT)",
        "answer": "The direct answer to the user's question. (Required for ANSWER)"
    }}
}}

**IMPORTANT**: Do not assume an action is impossible just because the element is not currently labeled. It may be visible elsewhere on the full-page screenshot. Prioritize scrolling if the target is not in the labeled view.

'''  # noqa: E501
        return prompt
