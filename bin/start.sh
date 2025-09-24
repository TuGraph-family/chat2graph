#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

# pre-check
pids=$(get_pids)
if [[ -n $pids ]]; then
  fatal "Chat2Graph server already started (pid: $pids)"
fi

# start MCP servers
echo "Starting MCP servers..."
bash start_mcp_server.sh

# prepare log path
mkdir -p "$(dirname ${SERVER_LOG_PATH})"

# create a new log file with a timestamp
timestamp=$(date +"%Y%m%d_%H%M%S")
new_server_log_path="$(dirname ${SERVER_LOG_PATH})/server_${timestamp}.log"
ln -sf "$new_server_log_path" "${SERVER_LOG_PATH}"

# startup python server
project_root=$(dirname "$(pwd)")
cd ${project_root} || exit 1
nohup python ${project_root}/app/server/bootstrap.py > "${new_server_log_path}" 2>&1 </dev/null &

# print startup logs
tail -f "${new_server_log_path}" | while IFS= read -r line
do
  if [[ "$line" == *"Press CTRL+C to quit"* ]]; then
      pkill -P $$ tail
      echo "Server detail logs in ${new_server_log_path}"
  else
    echo "$line"
  fi
done

# post-check
pids=$(get_pids)
if [[ -n $pids ]]; then
  info "Chat2Graph server started success ! (pid: $pids)"
else
  fatal "Chat2Graph server started failed, logs in ${new_server_log_path}"
fi
