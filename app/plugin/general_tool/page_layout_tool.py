import os
from pathlib import Path
from typing import List, Optional
import uuid

from mcp.types import ContentBlock

from app.core.model.task import ToolCallContext
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.mcp_service import McpService
from app.core.toolkit.tool import Tool
from app.plugin.general_tool.multi_modal_tool import MultiModalTool
from app.plugin.general_tool.url_downloader import UrlDownloaderTool


class PageLayoutTool(Tool):
    """Strategic Webpage Analyzer"""

    def __init__(self):
        super().__init__(
            name=self.visual_analyze_webpage_layout.__name__,
            description=self.visual_analyze_webpage_layout.__doc__ or "",
            function=self.visual_analyze_webpage_layout,
        )

    async def visual_analyze_webpage_layout(
        self,
        tool_call_ctx: ToolCallContext,
        task_description: str,
        url: str,
    ) -> str:
        """Analyzes a webpage's full vision layout to create a strategic interaction plan.

        Think of this tool as your "reconnaissance drone" or "advance scout" for a webpage.

        Before you start interacting with a complex page (clicking, scrolling, typing), use this tool
        to get a high-level "map" of the entire page. It analyzes a full-page screenshot to tell you:
        1.  What is the page for?
        2.  What obstacles (like cookie popups) are in your way?
        3.  Where are the key buttons, links, and inputs you need for your task?
        4.  But, since it is visual, it cannot tell you the very specific details like the ref or the x,y location, etc.

        Use this at the beginning of interacting with a new, important URL to form a solid plan.
        AVOID using this for simple, obvious pages or for every single step. It is a strategic,
        not a tactical, tool.

        Args:
            task_description (str): **CRITICAL:** Provide a high-level, strategic GOAL, not a low-level action.
                This description tells the analyst *what you ultimately want to achieve* on the page.

                - GOOD (Strategic Goal): "Find the login form to sign into the user account."
                - GOOD (Strategic Goal): "Locate the search bar and filters for finding articles from 2020."
                - GOOD (Strategic Goal): "Extract the titles and links of the top 5 news stories."

                - BAD (Low-level Action): "Click the button with index 5."
                - BAD (Low-level Action): "Scroll down."
                - BAD (Low-level Action): "Find the div with class 'main-content'."
            url (str): The URL of the webpage to analyze. This should be the current page you are viewing.

        Returns:
            str: A JSON formatted string containing a structured analysis of the webpage,
                    which you can use to build a step-by-step plan. Returns an error
                    message if the analysis fails.
        """  # noqa: E501

        # First, try to download the file directly.
        downloaded_file_path: Optional[Path] = None
        try:
            temp_dir = "./tmp/"
            os.makedirs(temp_dir, exist_ok=True)
            # Let UrlDownloaderTool handle the extension.
            save_path_base = os.path.join(temp_dir, str(uuid.uuid4()))
            downloaded_file_path = await UrlDownloaderTool().download_file_from_url(
                url=url,
                save_path=save_path_base,
            )
        except Exception as e:
            print(f"Direct download of {url} failed: {e}. Will try to render with browser.")

        pdf_path: Optional[str] = None
        if downloaded_file_path:
            pdf_path = str(downloaded_file_path)
            print(f"Successfully downloaded file from {url} to {pdf_path}")
        else:
            # If download failed or URL points to an HTML page, use browser to render.
            print(f"Falling back to browser rendering for {url}")
            try:
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
                    raise ValueError("MCP service (BrowserTool) not found in the toolkit.")

                mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)

                temp_dir = "./tmp/"
                os.makedirs(temp_dir, exist_ok=True)
                file_path: str = os.path.join(temp_dir, f"{uuid.uuid4()}.pdf")

                pdf_path_results: List[ContentBlock] = await mcp_connection.call(
                    tool_name="browser_export_whole_webpage_as_pdf",
                    file_path=file_path,
                )

                assert pdf_path_results and pdf_path_results[0].type == "text", (
                    "Expected a text content block with the file path."
                )
                pdf_path = pdf_path_results[0].text
                print(f"Successfully rendered page {url} to {pdf_path}")
            except Exception as browser_e:
                raise ValueError(f"Failed to render URL {url} with browser after direct download failed.") from browser_e

        if not pdf_path:
            raise ValueError(f"Could not retrieve content from URL {url} either by download or rendering.")

        structured_prompt = self._construct_layout_analysis_prompt(task_description)

        return await MultiModalTool().call_multi_modal(
            query_prompt=structured_prompt, media_paths=[pdf_path]
        )

    def _construct_layout_analysis_prompt(self, task_description: str) -> str:
        prompt = f"""
    You are an expert Web Page Layout Analyst. Your task is to analyze the provided webpage document (rendered as a PDF/image) and generate a structured JSON output to guide an automated agent. The agent's high-level goal is: "{task_description}".

    Analyze the entire page and provide a JSON object with the following schema. Adhere strictly to this structure. Do not add any explanatory text outside of the JSON object. And the JSON object will be later read by an agent, so the content should better be friendly understandable for the agent.

    ### JSON OUTPUT SCHEMA ###
    {{
    "analysis_summary": {{
        "page_purpose": "A brief, one-sentence summary of the page's main purpose (e.g., 'Login page', 'News article index', 'Product search results').",
        "is_goal_achievable": "A boolean indicating if the agent's goal ('{task_description}') seems achievable on this page.",
        "goal_achievability_reason": "A brief explanation for 'is_goal_achievable'."
    }},
    "obstacles": [
        {{
        "type": "string (e.g., 'Cookie Banner', 'Subscription Popup', 'Login Wall', 'Advertisement')",
        "location_description": "A description of its position (e.g., 'Floating at the bottom', 'Covers the top 20% of the page', 'Modal dialog in the center').",
        "dismiss_element_text": "The exact text on the button or link to close this obstacle (e.g., 'Accept all cookies', 'Close', 'X', 'No thanks'). Provide null if not found."
        }}
    ],
    "key_elements": [
        {{
        "element_description": "A unique description of a key interactive element relevant to the agent's goal. For example: 'Primary search input field', 'The 'Next Page' pagination button', 'User profile icon'.",
        "element_text": "The visible text of the element. For form inputs, this might be the placeholder text or label.",
        "element_type": "The type of element, such as 'button', 'link', 'input_text', 'checkbox', 'dropdown'.",
        "estimated_vertical_location": "A string describing its vertical position on the *entire page*: 'top', 'upper-middle', 'middle', 'lower-middle', 'bottom'."
        }}
    ]
    }}

    ### INSTRUCTIONS ###
    1.  **Obstacle Detection:** First, identify any elements that overlay the main content and block interaction. These are your top priority. Fill the `obstacles` array. If there are no obstacles, return an empty array `[]`.
    2.  **Key Element Identification:** Based on the agent's goal, identify all interactive elements (buttons, links, form fields) that are crucial for achieving the task. Populate the `key_elements` array.
        *   For a goal like "login", key elements would be the 'username' input, 'password' input, and 'login' button.
        *   For a goal like "find research papers from 2020", key elements would be the search bar, date filters, and the search button.
    3.  **Location Estimation:** For each key element, estimate its vertical position on the FULL page. This is critical for guiding the agent's scrolling. Use the five categories: 'top', 'upper-middle', 'middle', 'lower-middle', 'bottom'.
    4.  **Completeness:** Be thorough. If there are multiple relevant elements (e.g., several news headlines), list a representative sample. If a form has multiple fields, list them all.
    5.  **Strict JSON:** Your entire output must be a single, valid JSON object.

    Begin analysis now.
    """  # noqa: E501
        return prompt


def init_server():
    """Initialize the server by setting up the database and service factory."""
    from app.core.dal.dao.dao_factory import DaoFactory
    from app.core.dal.database import DbSession
    from app.core.dal.init_db import init_db
    from app.core.service.service_factory import ServiceFactory

    # Initialize the database
    init_db()

    # Initialize the DAO factory with a database session
    DaoFactory.initialize(DbSession())

    # Initialize the service factory
    ServiceFactory.initialize()


async def main():
    """Main function to run the AnalyzeWebPageLayoutTool."""
    init_server()

    tool = PageLayoutTool()
    url = "https://en.wikipedia.org/wiki/Clownfish"  # Replace with the actual URL to analyze
    task_description = "Introduce the species and find its habitat information."

    result = await tool.visual_analyze_webpage_layout(
        tool_call_ctx=ToolCallContext(job_id="1", operator_id="2"),
        url=url,
        task_description=task_description,
    )
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())