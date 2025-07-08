#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

# stop MCP tools
# echo "Stopping MCP servers..."
info "MCP servers is not stopped."
# bash stop_mcp_server.sh

pids=$(get_pids)
if [[ -n $pids ]]; then
  kill -9 $pids && info "Chat2Graph server stopped success !"
else
  warn "Chat2Graph server not found"
fi
