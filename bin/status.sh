#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && source utils.sh || exit

pids=$(get_pids)
if [[ -n $pids ]]; then
  info "Chat2Graph server is running (pid: $pids)"
else
  error "Chat2Graph server is stopped"
fi
