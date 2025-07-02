# Key Lesson:
# “尝试在不同的任务中退出取消范围”错误发生是因为 McpConnection 对象是在与其创建时不同的 asyncio 任务中被关闭的。
# 解决方案是将连接的整个生命周期（连接、使用、关闭）管理在同一个异步任务中，以确保资源管理在正确的上下文中进行。

# Deeper Explanation: The Root Cause of the "Cancel Scope" Error
#
# Q: Why did the original code fail, and what does it reveal about the underlying mechanics?
# A: The error is a direct consequence of how `asyncio`/`anyio` manages resource lifecycles
#    and how the `stdio` client is implemented.
#
# 1.  `stdio_client` is an `@asynccontextmanager`: Looking at the `mcp.client.stdio`
#     code, the `stdio_client` function is a context manager. This means it has a setup
#     phase (everything before `yield`) and a crucial teardown phase (the `finally` block).
#
# 2.  Resource Ownership is Task-Local: When `connection.connect()` was called inside a
#     newly created task (e.g., `Task 1`), that task "entered" the `stdio_client` context.
#     This action did two critical things:
#     a. It spawned a new child process (`npx @playwright/mcp...`).
#     b. It started background tasks to read/write from the process's stdin/stdout.
#     These resources are now "owned" by `Task 1`.
#
# 3.  The Violation: The original code returned the `connection` object from `Task 1`
#     to the `main` task. Later, the `main` task tried to call `connection.close()`.
#     This `close()` call attempts to trigger the teardown/`finally` block of the
#     `stdio_client` context manager.
#
# 4.  The Crash: The `anyio` framework detected that the `main` task was trying to exit a
#     context that was entered by a *different* task (`Task 1`). This is strictly
#     forbidden because it breaks structured concurrency. The teardown logic, which is
#     responsible for terminating the child process and cleaning up I/O streams, MUST
#     run in the same task that initiated it to guarantee order and prevent race
#     conditions or orphaned processes.
#
# Conclusion: The error was not just a simple bug but a safety mechanism firing as
# designed. It correctly prevented an unsafe operation where one task's resources
# (specifically, a live child process and its I/O handlers) were being improperly
# managed by another. The final, correct solution respects this by ensuring the task
# that creates the process is the same one that is responsible for terminating it.

# Additional Context: Synchronous vs. Asynchronous Execution
#
# Q: What would happen if this wasn't run with asyncio's concurrency?
# A: The key difference is parallel vs. sequential execution.
#
# 1.  Asynchronous (Current method): `asyncio.gather` starts all `run_connection_lifecycle`
#     tasks concurrently. Since each STDIO connection creates a new child process, this means
#     multiple `npx` processes are created and communicated with at roughly the same time.
#     The program efficiently switches between tasks when one is waiting for I/O (e.g., a
#     response from its child process). This is highly performant.
#
# 2.  Synchronous (Sequential): If we were to `await` each task in a simple `for` loop
#     instead of using `gather`, `run_connection_lifecycle(1)` would have to complete fully
#     (create process, connect, test, close, terminate process) before
#     `run_connection_lifecycle(2)` could even begin. The total execution time would be the
#     sum of all individual run times, which is much slower.
#
# Conclusion: Since each connection is an independent, I/O-bound process, `asyncio` is
# essential for managing them efficiently and achieving true concurrent testing.

import asyncio

from app.core.common.type import McpTransportType, ToolGroupType
from app.core.toolkit.mcp_connection import McpConnection
from app.core.toolkit.tool_config import McpConfig, McpTransportConfig


async def run_connection_lifecycle(connection_id: int):
    """Create, test, and close a single MCP connection."""
    print(f"🔗 Starting lifecycle for connection {connection_id}...")
    
    transport_config = McpTransportConfig(
        transport_type=McpTransportType.SSE,
        url="http://localhost:8931",
    )

    connection = McpConnection(McpConfig(
        type=ToolGroupType.MCP,
        name=f"Test MCP Service {connection_id}",
        transport_config=transport_config,
    ))

    try:
        # 1. Connect
        await connection.connect()
        print(f"✅ Connection {connection_id} established (ID: {connection.get_id()})")

        # 2. List available tools
        tools = await connection.list_tools()
        print(f"🔧 Connection {connection_id}: {len(tools)} tools available")
        
        # Print first few tool names to debug
        if connection_id == 1:  # Only print for first connection to avoid spam
            tool_names = [tool.name for tool in tools[:10]]
            print(f"🔍 Available tools: {tool_names}")

        # 3. Open a webpage
        test_urls = [
            "https://example.com",
            "https://httpbin.org/get", 
            "https://jsonplaceholder.typicode.com/posts/1",
            "https://github.com",
            "https://www.google.com"
        ]
        
        url = test_urls[(connection_id - 1) % len(test_urls)]
        print(f"🌐 Connection {connection_id}: Opening {url}...")
        
        # Use correct playwright tool names (common ones are navigate, get_title, close)
        try:
            # Use browser_navigate to open the page
            await connection.connect()  # Ensure connection is active
            result = await connection.call("browser_navigate", url=url)
            print(f"📄 Connection {connection_id}: Page opened successfully")
            
            # Try to get page title using a different tool name
            try:
                title_result = await connection.call("browser_get_title")
                print(f"📝 Connection {connection_id}: Page title - {title_result}")
            except Exception:
                # If browser_get_title doesn't exist, try other possible names
                try:
                    title_result = await connection.call("page_title")
                    print(f"📝 Connection {connection_id}: Page title - {title_result}")
                except Exception:
                    print(f"📝 Connection {connection_id}: Title tool not available, skipping...")
            
            # Close the browser using browser_close
            close_result = await connection.call("browser_close")
            print(f"🔒 Connection {connection_id}: Browser closed")
            
        except Exception as tool_error:
            print(f"⚠️ Connection {connection_id}: Tool call failed - {tool_error}")
            # Try alternative tool names
            try:
                result = await connection.call("playwright_goto", url=url)
                print(f"📄 Connection {connection_id}: Page opened with goto")
            except Exception as e2:
                print(f"⚠️ Connection {connection_id}: Alternative tool also failed - {e2}")

    except Exception as e:
        print(f"❌ Connection {connection_id} lifecycle failed: {e}")

    finally:
        # 4. Close connection
        try:
            print(f"🔒 Closing connection {connection_id} (ID: {connection.get_id()})...")
            await connection.close()
            print(f"✅ Connection {connection_id} closed")
        except Exception as e:
            print(f"❌ Connection {connection_id} cleanup failed: {e}")


async def main():
    """Test multiple concurrent MCP connection lifecycles."""
    print("🎭 Testing Multiple Concurrent Playwright MCP Connections")
    print("="*60)
    print("This test will run 5 concurrent connection lifecycles (create, test, close).")
    print("="*60)

    tasks = []
    for i in range(5):
        task = asyncio.create_task(run_connection_lifecycle(i + 1))
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)
    
    print("\n" + "="*60)
    print("🎯 TEST SUMMARY")
    print("="*60)
    print("✅ All concurrent connection lifecycle tests completed.")


if __name__ == "__main__":
    asyncio.run(main())
