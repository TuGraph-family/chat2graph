Config the MCP server for [File System](https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem):

```yaml
  - &file_tool
    name: "FileTool"
    type: "MCP"
    mcp_transport_config:
      transport_type: "STDIO"
      command: "npx"
      args: ["@modelcontextprotocol/server-filesystem", "/Users/username/Desktop", "/path/to/other/allowed/dir"]
```
