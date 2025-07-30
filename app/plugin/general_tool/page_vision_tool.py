import os
from pathlib import Path
from time import sleep
from typing import List, Optional
import uuid

from mcp.types import ContentBlock

from app.core.common.type import ToolGroupType
from app.core.model.task import ToolCallContext
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.mcp_service import McpService
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_config import (
    McpConfig,
    McpTransportConfig,
    McpTransportType,
)
from app.plugin.general_tool.multi_modal_tool import MultiModalTool
from app.plugin.general_tool.url_downloader import UrlDownloaderTool


class PageVisionTool(Tool):
    """A Visual Question Answering (VQA) tool for analyzing web pages."""

    def __init__(self):
        super().__init__(
            name=self.call_page_vision.__name__,
            description=self.call_page_vision.__doc__ or "",
            function=self.call_page_vision,
        )

    async def call_page_vision(
        self,
        tool_call_ctx: ToolCallContext,
        question: str,
        url: str,
    ) -> str:
        """Answers a wide range of questions about a webpage by visually analyzing its content.

        However, this tool is not perfect because the page layout is not always captured perfectly,
        and sometimes images cannot be rendered correctly.

        This tool functions as a Visual Large Model (VLM) expert for web pages. It takes a
        full-page screenshot and a question, then provides a structured answer based on what a
        human would see.

        Use this tool when you need to understand the visual layout, content within images, or
        complexly structured information that is difficult to parse from HTML alone.

        Args:
            question (str): **CRITICAL:** A clear and specific question about the visual content of the page.
                The more specific the question, the better the answer.

                - GOOD (Extraction): "What is the current temperature shown for New York?"
                - GOOD (Description): "Describe the color scheme and layout of the page."
                - GOOD (Verification): "Does the page contain a map?"
                - GOOD (Summarization): "Summarize the key points from the infographic about climate change."

                - BAD (Too Vague): "Analyze this page."
                - BAD (Action-Oriented): "Click on the third link."
                - BAD (Code-Specific): "Find the element with id 'user-profile'."
            url (str): The URL of the webpage to analyze.

        Returns:
            str: A JSON formatted string containing a direct answer to the question, along with supporting evidence
                 and an assessment of whether the question was answerable from the visual content.
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

        structured_prompt = self._construct_visual_query_prompt(question)

        return await MultiModalTool().call_multi_modal(
            query_prompt=structured_prompt, media_paths=[pdf_path]
        )

    def _construct_visual_query_prompt(self, question: str) -> str:
        prompt = f"""
    You are an expert Visual Question Answering (VQA) agent specializing in analyzing web pages. Your task is to act as a user's eyes, meticulously examining the provided webpage document (rendered as a PDF/image) and answering a specific question about its visual content.

    The user's question is: "{question}"

    You must provide your response in a structured JSON format. Adhere strictly to the schema below. Do not add any explanatory text outside the single JSON object.

    ### JSON OUTPUT SCHEMA ###
    {{
        "thinking": "Your thought process on how you arrived at the answer. This should be a brief explanation of your reasoning.",
        "reason": "If 'is_question_answerable' is false, provide a brief explanation (e.g., 'The page does not contain the requested chart.', 'The text is too blurry to read.'). If true, this can be null.",
        "summary_of_evidence": "A brief description of where you found the information on the page. Be specific about the visual location and context (e.g., 'From the pricing table in the middle of the page.', 'From the text inside the main banner at the top.', 'Based on the overall layout and imagery.'). If not answerable, this must be null.",
        "is_question_answerable": "A boolean indicating if the information required to answer the question is visually present on the page.",
        "answer": "The direct answer to the user's question. The format of the answer should match the question type (e.g., a string for a description, a number for a price, a boolean for a yes/no question, a list of strings for multiple items). If the question is not answerable, this must be null.",
    }}

    ### INSTRUCTIONS ###
    1.  **Understand the Question's Intent:** First, carefully analyze the user's question to understand what kind of answer is expected (e.g., an extraction, a description, a yes/no verification, a summary).
    2.  **Scan the Document:** Visually inspect the entire document to find the relevant information. Look at text, images, tables, charts, layout, and all other visual elements.
    3.  **Formulate the Answer:**
        *   If you can answer the question, set `is_question_answerable` to `true`.
        *   Construct the answer in the `answer` field, ensuring its data type is appropriate for the question. For example:
            *   For "Is there a map?", `answer` could be `true`.
            *   For "List the social media links.", `answer` could be `["twitter.com/...", "linkedin.com/..."]`.
            *   For "Describe the homepage.", `answer` should be a descriptive string.
        *   Provide the location of your finding in the `summary_of_evidence` field.
    4.  **Handle Unanswerable Questions:**
        *   If the information is not present or the question cannot be answered from the visual content, set `is_question_answerable` to `false`.
        *   Explain why in the `reason` field.
        *   Set `answer` and `summary_of_evidence` to `null`.
    5.  **Strict JSON:** Your entire output must be a single, valid JSON object.

    Begin your visual analysis now.
    """  # noqa: E501
        return prompt


async def init_server():
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

    toolkit_service: ToolkitService = ToolkitService.instance

    mcp_service = McpService(
        mcp_config=McpConfig(
            type=ToolGroupType.MCP,
            name="BrowserTool",
            transport_config=McpTransportConfig(
                transport_type=McpTransportType.STDIO,
                command="uvx",
                args=["browser-use", "--mcp"],
            ),
        )
    )
    test_action = Action(
        id="test_action",
        name="Test Action",
        description="A test action to verify the MCP service.",
        next_action_ids=[],
    )
    toolkit_service.add_action(test_action, [], [])
    toolkit_service.add_tool_group(mcp_service, [(test_action, 1.0)])

    tool_call_ctx = ToolCallContext(job_id="1", operator_id="2")
    mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)

    await mcp_connection.call(
        tool_name="browser_navigate",
        url="http://pietromurano.org/Papers/Murano-Khan-Published-Version.pdf",
    )
    sleep(2)

    await mcp_connection.call(tool_name="browser_get_state")

async def close_connection():
    """Close the MCP connection."""
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
        raise ValueError("MCP service not found in the toolkit.")
    tool_call_ctx = ToolCallContext(job_id="1", operator_id="2")
    mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)

    await mcp_connection.close()


async def main():
    """Main function to run the AnalyzeWebPageLayoutTool."""
    await init_server()

    tool = PageVisionTool()
    task_description = "Introduce the information."

    result = await tool.call_page_vision(
        tool_call_ctx=ToolCallContext(job_id="1", operator_id="2"),
        question=task_description,
        url="http://pietromurano.org/Papers/Murano-Khan-Published-Version.pdf",
    )
    print(result)

    await close_connection()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())