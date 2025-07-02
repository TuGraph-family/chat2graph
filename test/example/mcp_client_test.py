import asyncio
import logging

from app.core.common.type import McpTransportType
from app.core.toolkit.mcp_service import McpService, McpTransportConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main function demonstrating MCP client and tools usage."""

    # Create single shared MCP transport configuration
    transport_config = McpTransportConfig(
        transport_type=McpTransportType.STDIO,
        command="npx",
        args=["@playwright/mcp@latest", "--isolated"],
    )

    # Create single shared MCP client
    shared_client = McpService(transport_config=transport_config, name="Shared Browser MCP Client")

    try:
        # Connect once
        await shared_client.connect()
        logger.info("Shared MCP client connected successfully")

        # List available tools
        available_tools = await shared_client.list_tools()
        logger.info(f"Available tools: {[tool.name for tool in available_tools]}")

        # Both tools use the same client
        async def call_tool_1():
            """Call first browser tool - navigate to Python docs."""
            try:
                logger.info("Calling browser navigation tool...")
                result = await shared_client.call_tool(
                    "browser_navigate",
                    url="https://docs.python.org"
                )
                logger.info(f"Tool 1 result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in tool 1: {e}")
                return None

        async def call_tool_2():
            """Call second browser tool - navigate to GitHub and take screenshot."""
            try:
                logger.info("Calling browser navigation tool for GitHub...")
                
                # Navigate to a different URL (reuses same browser instance)
                await shared_client.call_tool(
                    "browser_navigate",
                    url="https://github.com"
                )
                logger.info("Navigation completed, taking screenshot...")
                
                # Take screenshot of current page
                result = await shared_client.call_tool(
                    "browser_take_screenshot"
                )
                logger.info(f"Tool 2 result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in tool 2: {e}")
                return None

        # Can even run concurrently now since it's the same client
        logger.info("Starting sequential tool calls...")

        result1 = await call_tool_1()
        result2 = await call_tool_2()

        results = [result1, result2]

        logger.info("Tool calls completed")
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                logger.error(f"Tool {i} failed with exception: {result}")
            else:
                logger.info(f"Tool {i} completed successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")

    finally:
        # Clean up - aclose single client
        try:
            await shared_client.aclose()
            logger.info("Shared MCP client disconnected")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    asyncio.run(main())
