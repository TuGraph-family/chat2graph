#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

# load MCP server configuration
source mcp_server_config.sh

# stop each MCP tool
for config in "${mcp_tools_config[@]}"; do
    mcp_name=$(get_mcp_name "$config")
    port=$(get_mcp_port "$config")

    # find processes by port (most reliable method)
    mcp_pids=$(lsof -ti:${port} 2>/dev/null)

    if [[ -n $mcp_pids ]]; then
        kill -9 $mcp_pids && info "${mcp_name} MCP tool stopped success !"
    else
        warn "${mcp_name} MCP tool not found"
    fi
done
