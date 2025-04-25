#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

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

project_root=$(dirname "$(pwd)")
lock_file="/tmp/chat2graph.lock"

acquire_lock $lock_file
check_env
build_python $project_root
build_web $project_root
release_lock $lock_file

info "Build success !"
