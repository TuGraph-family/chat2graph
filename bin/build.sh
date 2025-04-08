#!/bin/bash

check_command() {
    local cmd_name=$1
    local awk_col=$2
    local awk_f=$3

    local path=$(which "$cmd_name" 2>/dev/null)
    if [[ -n $path ]]; then
        local version_cmd="$cmd_name --version 2>/dev/null"
        if [[ -n $awk_col ]]; then
          awk_cmd="awk"
          if [[ -n $awk_f ]]; then
            awk_cmd="$awk_cmd -F '$awk_f'"
          fi
          awk_cmd="$awk_cmd '{print \$$awk_col}'"
          version_cmd="$version_cmd | $awk_cmd"
        fi
        local version=$(eval $version_cmd)
        echo -e "* $cmd_name \033[32m$version\033[0m $path"
        return 0
    else
        echo -e "* $cmd_name \033[31m[NOT INSTALLED]\033[0m"
        return 1
    fi
}

info() {
  if [[ -n $1 ]]; then
    echo -e "\033[32m$1\033[0m"
  fi
}

error() {
  if [[ -n $1 ]]; then
    echo -e "\033[31m$1\033[0m"
  fi
  return 1
}

fatal() {
  error "$1"; exit 1
}

check_env() {
  info "Checking environment:"
  check_command python 2 || fatal
  check_command pip 2 || fatal
  check_command poetry 3 ' |)' || fatal "Run with 'pip install poetry' and retry."
  check_command node 2 'v' || fatal
  check_command npm || fatal
}

build_python() {
  app_dir=$1

  cd ${app_dir}
  info "Installing python packages: ${app_dir}"
  poetry lock && poetry install || fatal "Failed to install python packages"
}

build_web() {
  project_dir=$1
  web_dir=${project_dir}/web
  server_web_dir=${project_dir}/app/server/web

  cd ${web_dir}
  info "Building web packages: ${web_dir}"

  npm cache clean --force && npm install || fatal "Failed to install web packages"

  npm run build || fatal "Failed to build web packages"

  rm -rf ${server_web_dir} && cp -r ${web_dir}/dist ${server_web_dir} \
  || fatal "Failed to move web packages"
}

main() {
  project_dir=$(cd $(dirname $(dirname $0)); pwd)

  check_env
  build_python $project_dir
  build_web $project_dir

  info "Build success !"
}

main
