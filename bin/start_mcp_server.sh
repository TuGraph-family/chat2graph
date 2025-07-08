#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

# load MCP server configuration
source mcp_server_config.sh

mkdir -p "$(dirname ${MCP_LOG_PATH})"

timestamp=$(date +"%Y%m%d_%H%M%S")
new_mcp_log_path="$(dirname ${MCP_LOG_PATH})/mcp_${timestamp}.log"
ln -sf "$new_mcp_log_path" "${MCP_LOG_PATH}"

# start each MCP tool
for config in "${mcp_tools_config[@]}"; do
    mcp_name=$(get_mcp_name "$config")
    port=$(get_mcp_port "$config")
    command=$(get_mcp_command "$config")

    # check if the port is in use
    if lsof -i :$port > /dev/null; then
        info "Port $port is already in use. Assuming ${mcp_name} is running."
        continue
    fi

    # check if the process is already running
    if pgrep -f "$command --port $port" > /dev/null; then
        info "${mcp_name} MCP tool is already running."
        continue
    fi

    nohup ${command} --port ${port} >> "${new_mcp_log_path}" 2>&1 </dev/null &
    pid=$!

    # wait a moment to see if the process started successfully
    sleep 2

    if ps -p $pid > /dev/null; then
        info "${mcp_name} MCP tool started successfully! (pid: $pid)"
    else
        error "Failed to start ${mcp_name} MCP tool. Check the log for details: ${new_mcp_log_path}"
    fi
done

echo "MCP tools logs in ${new_mcp_log_path}"
