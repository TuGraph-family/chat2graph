Run the MCP server for [Playwright](https://github.com/microsoft/playwright-mcp):

```bash
npx @playwright/mcp@latest --port 8931
```

Example code to create a tool that uses the MCP server:

```python
browsing_tool = McpTool(
    id="playwright_browsing_tool",
    transport_config=McpTransportConfig(
        transport_type=McpTransportType.SSE,
        url="http://localhost:8931/sse",
    )
)
```