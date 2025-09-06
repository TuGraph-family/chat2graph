import os
from typing import Any, Dict, List, Optional, Union
import uuid

from mcp.types import EmbeddedResource, ImageContent, TextContent

from app.core.model.task import ToolCallContext
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.mcp.mcp_service import McpService
from app.core.toolkit.system_tool.gemini_multi_modal_tool import GeminiMultiModalTool
from app.core.toolkit.tool import Tool


class PageVisionTool(Tool):
    """A Visual Question Answering (VQA) tool for analyzing web pages.

    Node: make sure the BrowserTool is properly configured in the MCP service.
    """

    def __init__(self):
        super().__init__(
            name=self.browser_read_page_by_vision.__name__,
            description=self.browser_read_page_by_vision.__doc__ or "",
            function=self.browser_read_page_by_vision,
        )

    async def browser_read_page_by_vision(
        self, tool_call_ctx: ToolCallContext, llm_prompt: str
    ) -> str:
        """Answers complex questions or llm prompts about a webpage by visually analyzing its content like a human.

        **When to Use This Tool:**
        This tool is your "eyes" for a webpage. Use it when:
        - You need to understand the layout, structure, or visual hierarchy (e.g., "What is the most prominent button on the page?", "Is there a sidebar on the right?").
        - You need to interpret visual data like charts, graphs, or infographics.
        - You need to verify the presence of visual elements ("Is there a shopping cart icon at the top?").
        - When you use it and `browser_get_interactive_elements_info` tool.
        - ...

        **How to Formulate Effective Questions:**
        The key is to ask questions or provide llm prompt from the perspective of a human looking at the page. Be descriptive and specific. Instead of just asking for a piece of text you failed to find, ask the tool to *look* for it and describe where it is.

        Input Schema (Args):
        {
            "type": "object",
            "properties": {
                "llm_prompt": {
                    "type": "str",
                    "description": "**CRITICAL:** A clear, specific llm prompt about the visual content. The more context you provide in the question, the better the VLM can understand the task.\n**STRATEGIC EXAMPLES:**\n- **When text extraction fails:** Instead of just re-trying to extract, ask: \"I'm looking for the price of the 'Pro Plan'. I couldn't find it in the HTML. Can you visually scan the page for a pricing table or section and tell me the price for the 'Pro Plan'?\"\n- **For layout understanding:** \"Describe the main sections of the homepage. What is in the main banner?\"\n- **For chart analysis:** \"There should be a bar chart showing monthly sales. What are the approximate sales for August?\"\n- **For verification:** \"Is there a 'Live Chat' support widget visible on the page? If so, where is it located?\"\n\n**AVOID:**\n- Vague questions: \"Analyze this page.\"\n- Action commands: \"Click the login button.\"\n- Code-level questions: \"Find the div with class 'main-content'.\""
                },
            },
            "required": [
                "llm_prompt"
            ]
        }
        """  # noqa: E501
        pdf_path: Optional[str] = None

        try:
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

            # prepare the PDF path
            temp_dir = "./.gaia_tmp/"
            os.makedirs(temp_dir, exist_ok=True)
            file_path: str = os.path.join(temp_dir, f"{uuid.uuid4()}.pdf")

            # use browser to render
            browser_tool_args: Dict[str, Any] = {"file_path": file_path}
            pdf_path_results: List[
                Union[TextContent, ImageContent, EmbeddedResource]
            ] = await mcp_connection.call(
                tool_name="browser_export_whole_webpage_as_pdf", **browser_tool_args
            )
            assert pdf_path_results and isinstance(pdf_path_results[0], TextContent), (
                "Expected a text content block with the file path."
            )
            pdf_path = pdf_path_results[0].text
            print(f"Successfully rendered page to {pdf_path}")
        except Exception as browser_e:
            raise ValueError(
                "Failed to render page with browser after direct download failed."
            ) from browser_e

        if not pdf_path:
            raise ValueError(
                "Could not retrieve content from page either by download or rendering."
            )

        structured_prompt = self._get_visual_query_prompt(llm_prompt)

        return await GeminiMultiModalTool().call_multi_modal(
            query_prompt=structured_prompt, media_paths=[pdf_path]
        )

    def _get_visual_query_prompt(self, question: str) -> str:
        prompt = f"""You are an expert Visual Question Answering (VQA) agent specializing in analyzing web pages. Your task is to act as a user's eyes, meticulously examining the provided webpage document (rendered as a PDF/image) and answering a specific question about its visual content.

    The user's question is: "{question}"

    You must provide your response in a structured JSON format. Adhere strictly to the schema below. Do not add any explanatory text outside the single JSON object.

    ### JSON OUTPUT SCHEMA ###
    {{
        "thinking": "Your thought process on how you arrived at the answer. This should be a brief explanation of your reasoning.",
        "reason": "If 'is_question_answerable' is false, provide a direct explanation for why the information is not available (e.g., 'The requested chart is not on the page.', 'The text is unreadable.'). If true, this can be null.",
        "speculated_reason": "If 'is_question_answerable' is false, provide a speculative reason for why the information might be missing or where it could potentially be found (e.g., 'The information might be on a different page, such as the "About Us" section.', 'The content may require a user to be logged in.'). If true, this must be null.",
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
        *   Explain the direct reason in the `reason` field.
        *   Provide a speculative reason in the `speculated_reason` field.
        *   Set `answer` and `summary_of_evidence` to `null`.
    5.  **Strict JSON:** Your entire output must be a single, valid JSON object.

    Begin your visual analysis now.
    """  # noqa: E501
        return prompt
