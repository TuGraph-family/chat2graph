#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && source utils.sh || exit

# load MCP server configuration
source mcp_server_config.sh

mkdir -p "$(dirname ${MCP_LOG_PATH})"

timestamp=$(date +"%Y%m%d_%H%M%S")
new_mcp_log_path="$(dirname ${MCP_LOG_PATH})/mcp_${timestamp}.log"
ln -sf "$new_mcp_log_path" "${MCP_LOG_PATH}"

is_port_in_use() {
    local port=$1
    # try with lsof (macOS, Linux)
    if command -v lsof >/dev/null; then
        if lsof -i :$port >/dev/null; then return 0; else return 1; fi
    fi
    # try with ss (modern Linux)
    if command -v ss >/dev/null; then
        if ss -tuln | grep -q ":$port "; then return 0; else return 1; fi
    fi
    # try with netstat (Linux, macOS, etc.)
    if command -v netstat >/dev/null; then
        if netstat -tuln | grep -q ":$port "; then return 0; else return 1; fi
    fi
    warning "Could not find lsof, ss, or netstat to check port status. Assuming port is free."
    return 1 # assume port is not in use
}

# check if there are any MCP servers to start
if [ ${#mcp_server_configs[@]} -eq 0 ]; then
    info "No MCP servers configured to start."
    exit 0
fi

# start each MCP server
for config in "${mcp_server_configs[@]}"; do
    mcp_name=$(get_mcp_name "$config")
    port=$(get_mcp_port "$config")
    command=$(get_mcp_command "$config")

    # check if the port is in use
    if is_port_in_use $port; then
        info "Port $port is already in use. Assuming ${mcp_name} is running."
        continue
    fi

    # check if the process is already running
    if pgrep -f "$command --port $port" > /dev/null; then
        info "${mcp_name} MCP server is already running."
        continue
    fi

    nohup ${command} --port ${port} >> "${new_mcp_log_path}" 2>&1 </dev/null &
    pid=$!

    # wait a moment to see if the process started successfully
    sleep 2

    if ps -p $pid > /dev/null; then
        info "${mcp_name} MCP server started successfully! (pid: $pid)"
    else
        error "Failed to start ${mcp_name} MCP server. Check the log for details: ${new_mcp_log_path}"
    fi
done

echo "MCP servers logs in ${new_mcp_log_path}"
