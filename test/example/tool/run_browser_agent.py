import asyncio
import pprint
from typing import Optional
from uuid import uuid4

from app.core.common.type import ToolGroupType
from app.core.dal.dao.dao_factory import DaoFactory
from app.core.dal.database import DbSession
from app.core.dal.init_db import init_db
from app.core.model.task import ToolCallContext
from app.core.service.service_factory import ServiceFactory
from app.core.service.toolkit_service import ToolkitService
from app.core.toolkit.action import Action
from app.core.toolkit.mcp.mcp_service import McpService
from app.core.toolkit.system_tool.browser_agent_tool import BrowserAgentTool
from app.core.toolkit.tool import Tool
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig, McpTransportType
from app.core.toolkit.tool_connection import ToolConnection


async def init_server() -> ToolConnection:
    """Initialize the server by setting up the database and service factory."""

    # initialize the database
    init_db()

    # initialize the DAO factory with a database session
    DaoFactory.initialize(DbSession())

    # initialize the service factory
    ServiceFactory.initialize()

    toolkit_service: ToolkitService = ToolkitService.instance

    browser_agent_tool = BrowserAgentTool()
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
    toolkit_service.add_tool(browser_agent_tool, [(test_action, 1.0)])
    toolkit_service.add_tool_group(mcp_service, [(test_action, 1.0)])

    return await mcp_service.create_connection(
        tool_call_ctx=ToolCallContext(job_id=str(uuid4()), operator_id=str(uuid4()))
    )

async def close_server(mcp_connection: ToolConnection):
    """Close the server and clean up resources."""
    await mcp_connection.close()

def get_browser_agent_tool() -> Tool:
    """Get the browser agent tool."""
    toolkit_service: ToolkitService = ToolkitService.instance
    toolkit = toolkit_service.get_toolkit()
    tool: Optional[Tool] = None
    for item_id in toolkit.vertices():
        tool = toolkit.get_tool(item_id)
        if tool and isinstance(tool, Tool):
            if tool.name == "assign_task_to_browser_agent":
                break

    if not tool:
        raise RuntimeError(
            "BrowserAgentTool 'assign_task_to_browser_agent' not found in toolkit. "
            "Ensure it was added via toolkit_service.add_tool(...) before calling "
            "get_browser_agent_tool()."
        )
    return tool

async def main():
    """An example of how to use the BrowserAgentTool to perform a simple web browsing task,
    following the required task_description format.
    """
    mcp_connection = await init_server()
    tool = get_browser_agent_tool()

    # define a simple, self-contained task for the browser agent.
    task_description = '''
TASK: Navigate to https://gemini.google.com/ and extract the main headline text.
TASK_CONTEXT: The headline is the most prominent text at the top of the page. Return only the text content of the headline as a plain string.
'''  # noqa: E501

    print("--- Assigning Task to Browser Agent ---")
    print(f"Task Description:\n{task_description}")

    # open a browser to simulate the real browsing agent environment
    await mcp_connection.call(tool_name="browser_navigate", url="https://www.google.com/")

    # call the tool to execute the task
    # this will spawn a separate agent process to perform the browsing and extraction
    result = await tool.function(task_description=task_description)

    print("\n--- Task Result ---")
    pprint.pprint(result)

    if result.get("success") and result.get("log_file"):
        print(f"\nBrowser agent execution logs can be found at: {result['log_file']}")

    await close_server(mcp_connection)


if __name__ == "__main__":
    asyncio.run(main())