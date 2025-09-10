import asyncio
from time import sleep
from typing import Optional, cast
from uuid import uuid4

from mcp.types import TextContent

from app.core.common.type import ToolGroupType
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.dal.init_db import init_db
from app.core.model.task import ToolCallContext
from app.core.service.service_factory import ServiceFactory
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.mcp.mcp_connection import McpConnection
from app.core.toolkit.mcp.mcp_service import McpService
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig, McpTransportType
from app.plugin.mcp.page_vision_tool import PageVisionTool


async def init_server(tool_call_ctx: ToolCallContext):
    """Initialize the server by setting up the database and service factory."""

    # initialize the database
    init_db()

    # initialize the DAO factory with a database session
    DaoFactory.initialize(DbSession())

    # initialize the service factory
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

    mcp_connection = cast(
        McpConnection,
        await mcp_service.create_connection(tool_call_ctx=tool_call_ctx),
    )

    await mcp_connection.call(
        tool_name="browser_navigate", url="https://www.youtube.com/watch?v=28QvSs2_zec/"
    )
    sleep(2)

    page_info = cast(
        TextContent,
        (await mcp_connection.call(tool_name="browser_get_interactive_elements_info"))[0],
    )
    print(page_info.text)
    sleep(2)


async def close_connection(tool_call_ctx: ToolCallContext):
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

    mcp_connection = await mcp_service.create_connection(tool_call_ctx=tool_call_ctx)
    await mcp_connection.close()


async def read_page_by_vision(tool_call_ctx: ToolCallContext):
    """Read the web page content using vision."""
    tool = PageVisionTool()
    task_description = "Introduce the information."

    result = await tool.browser_read_page_by_vision(
        tool_call_ctx=tool_call_ctx, llm_prompt=task_description
    )
    print(result)


async def main():
    """Main function to run the AnalyzeWebPageLayoutTool."""
    tool_call_ctx = ToolCallContext(job_id=str(uuid4()), operator_id=str(uuid4()))
    await init_server(tool_call_ctx=tool_call_ctx)
    await read_page_by_vision(tool_call_ctx=tool_call_ctx)
    await close_connection(tool_call_ctx=tool_call_ctx)


if __name__ == "__main__":
    asyncio.run(main())