#!/usr/bin/env bash

SERVER_LOG_PATH=~/.chat2graph/logs/server.log

info() {
  if [[ -n $1 ]]; then
    echo -e "\033[32m$1\033[0m"
  fi
}

warn() {
  if [[ -n $1 ]]; then
    echo -e "\033[33m$1\033[0m" >&2
  fi
  return 1
}

error() {
  if [[ -n $1 ]]; then
    echo -e "\033[31m$1\033[0m" >&2
  fi
  return 1
}

fatal() {
  error "$1"; exit 1
}

check_command() {
    cmd_name=$1
    awk_col=$2
    awk_f=$3

    path=$(which "$cmd_name" 2>/dev/null)
    if [[ -n $path ]]; then
        version_cmd="$cmd_name --version 2>/dev/null"
        if [[ -n $awk_col ]]; then
          awk_cmd="awk"
          if [[ -n $awk_f ]]; then
            awk_cmd="$awk_cmd -F '$awk_f'"
          fi
          awk_cmd="$awk_cmd '{print \$$awk_col}'"
          version_cmd="$version_cmd | $awk_cmd"
        fi
        version=$(eval $version_cmd)
        echo -e "* $cmd_name \033[32m$version\033[0m $path"
        return 0
    else
        echo -e "* $cmd_name \033[31m[NOT INSTALLED]\033[0m"
        return 1
    fi
}

get_pids() {
  cmd="/chat2graph/app/server/bootstrap.py"
  pids=$(ps aux | grep $cmd | grep -v grep | awk '{print$2}' | xargs)
  echo $pids
}

acquire_lock() {
  lock_file=$1
  if [[ -z $lock_file ]]; then
    fatal "Argument 'lock_file' is required"
  fi

  if [[ -e "$lock_file" ]]; then
    fatal "File $lock_file is locked by $(cat $lock_file)"
  fi

  if ! touch "$lock_file" 2>/dev/null; then
    fatal "Failed to lock file $lock_file"
  fi

  echo $$ > $lock_file
}

release_lock() {
  lock_file=$1
  if [[ -z $lock_file ]]; then
    fatal "Argument 'lock_file' is required"
  fi

  if [[ -f "$lock_file" ]]; then
    locked_pid=$(cat $lock_file)
    if [[ $$ == "$locked_pid" ]]; then
      rm $lock_file
    else
      fatal "File $lock_file is locked by $locked_pid"
    fi
  fi
}