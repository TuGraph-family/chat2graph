import asyncio
from time import sleep
from typing import Optional, cast
from uuid import uuid4

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
from app.plugin.mcp.browser_read_and_get_state import BrowserReadAndGetStateTool


async def init_server(tool_call_ctx: ToolCallContext, url: str):
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

    await mcp_connection.call(tool_name="browser_navigate", url=url)
    sleep(2)
    await mcp_connection.call(tool_name="browser_scroll", direction="down")
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

async def read_and_get_state(tool_call_ctx: ToolCallContext, vlm_task: str):
    """Read the current state of the browser."""
    # instantiate and call the ReadAndGetStateTool
    read_and_get_state_tool = BrowserReadAndGetStateTool()
    result = await read_and_get_state_tool.browser_read_and_get_state(
        tool_call_ctx=tool_call_ctx,
        vlm_task=vlm_task,
    )
    print(result)


async def main():
    """Main function to run the ReadAndGetStateTool."""
    tool_call_ctx = ToolCallContext(job_id=str(uuid4()), operator_id=str(uuid4()))
    await init_server(tool_call_ctx=tool_call_ctx, url="https://en.wikipedia.org/wiki/Tokyo")
    await read_and_get_state(
        tool_call_ctx=tool_call_ctx,
        vlm_task="As of 1987, which cities/states were sister cities/states with Tokyo?",
    )
    await close_connection(tool_call_ctx=tool_call_ctx)


if __name__ == "__main__":
    asyncio.run(main())
