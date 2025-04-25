#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

# pre-check
pids=$(get_pids)
if [[ -n $pids ]]; then
  fatal "Chat2Graph server already started (pid: $pids)"
fi

# prepare log path
mkdir -p "$(dirname ${SERVER_LOG_PATH})"

# startup python server
project_root=$(dirname "$(pwd)")
cd ${project_root} || exit 1
nohup python ${project_root}/app/server/bootstrap.py &> ${SERVER_LOG_PATH} </dev/null &

# print startup logs
tail -f "${SERVER_LOG_PATH}" | while IFS= read -r line
do
  if [[ "$line" == *"Press CTRL+C to quit"* ]]; then
      pkill -P $$ tail
      echo "Detail logs in ${SERVER_LOG_PATH}"
  else
    echo "$line"
  fi
done

# post-check
pids=$(get_pids)
if [[ -n $pids ]]; then
  info "Chat2Graph server started success ! (pid: $pids)"
else
  fatal "Chat2Graph server started failed, logs in ${SERVER_LOG_PATH}"
fi
