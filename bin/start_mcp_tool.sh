#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

# load MCP configuration
source mcp_config.sh

mkdir -p "$(dirname ${MCP_LOG_PATH})"

timestamp=$(date +"%Y%m%d_%H%M%S")
new_mcp_log_path="$(dirname ${MCP_LOG_PATH})/mcp_${timestamp}.log"
ln -sf "$new_mcp_log_path" "${MCP_LOG_PATH}"

# start each MCP tool
for config in "${mcp_tools_config[@]}"; do
    mcp_name=$(get_mcp_name "$config")
    port=$(get_mcp_port "$config")
    command=$(get_mcp_command "$config")

    # post check
    mcp_pids=$(lsof -ti:${port} 2>/dev/null)

    if [[ -n $mcp_pids ]]; then
        info "${mcp_name} MCP tool already started (pid: $mcp_pids)"
    else
        nohup ${command} --port ${port} >> "${new_mcp_log_path}" 2>&1 </dev/null &
        info "${mcp_name} MCP tool started success ! (pid: $!)"
    fi
done

echo "MCP tools logs in ${new_mcp_log_path}"
