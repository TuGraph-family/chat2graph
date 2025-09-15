import asyncio
from typing import cast
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


async def init_server() -> McpConnection:
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

    tool_call_ctx = ToolCallContext(job_id=str(uuid4()), operator_id=str(uuid4()))
    mcp_connection = cast(
        McpConnection,
        await mcp_service.create_connection(tool_call_ctx=tool_call_ctx),
    )
    return mcp_connection

async def close_connection(mcp_connection: McpConnection):
    """Close the MCP connection."""
    await mcp_connection.close()

async def browser_download_pdf(mcp_connection:McpConnection, url: str, file_path: str):
    """Read the current state of the browser."""
    save_path = cast(TextContent, (await mcp_connection.call(
        tool_name="browser_download_pdf",
        url=url,
        file_path=file_path,
    ))[0])
    print(f"Browser download PDF response: {save_path.text}")

async def main():
    """Main function to run the ReadAndGetStateTool."""
    mcp_connection = await init_server()
    await browser_download_pdf(
        mcp_connection=mcp_connection,
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7995278/pdf/zr-42-2-227.pdf",
        file_path="./.gaia_tmp/downloaded_pdf_1.pdf",
    )
    await browser_download_pdf(
        mcp_connection=mcp_connection,
        url="https://www.biorxiv.org/content/10.1101/2025.09.03.672144v2.full.pdf",
        file_path="./.gaia_tmp/downloaded_pdf_2.pdf",
    )
    await browser_download_pdf(
        mcp_connection=mcp_connection,
        url="https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0123456&type=printable",
        file_path="./.gaia_tmp/downloaded_pdf_3.pdf",
    )
    await browser_download_pdf(
        mcp_connection=mcp_connection,
        url="https://www.mdpi.com/2304-8158/8/10/484/pdf",
        file_path="./.gaia_tmp/downloaded_pdf_4.pdf",
    )
    await close_connection(mcp_connection=mcp_connection)


if __name__ == "__main__":
    asyncio.run(main())
