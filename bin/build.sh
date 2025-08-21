#!/usr/bin/env bash
cd "$(dirname "$(readlink -f "$0")")" &> /dev/null && source utils.sh || exit

check_env() {
  info "Checking environment:"
  check_command python 2 || fatal

  python -c 'import sys; exit(0 if (3, 10) <= sys.version_info < (3, 12) else 1)' \
    || fatal "Python version must be >=3.10 and <3.12. Found $(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  check_command pip 2 || fatal
  check_command poetry 3 ' |)' || fatal "Run with 'pip install poetry' and retry."
  check_command node 2 'v' || fatal
  check_command npm || fatal

  info "Checking for libmagic..."
  local os_type
  os_type=$(uname -s)
  local instal_libmagic_cmd=""

  if [[ "$os_type" == "Darwin" ]]; then # macOS
    if ! brew list libmagic &>/dev/null; then
      instal_libmagic_cmd="brew install libmagic"
    fi
  elif [[ "$os_type" == "Linux" ]]; then # Linux
    if ! dpkg -s libmagic1 &>/dev/null; then # Debian/Ubuntu
      instal_libmagic_cmd="sudo apt-get update && sudo apt-get install -y libmagic1"
    fi
  elif [[ "$os_type" == MINGW64* || "$os_type" == CYGWIN* ]]; then # Windows
    warn "Windows support for libmagic is not automated. Please install it manually."
  fi

  if [[ -n "$instal_libmagic_cmd" ]]; then
    read -t 30 -p "libmagic is not found. Do you want to install it now? (y/n): " -r response
    echo
    if [[ "$response" =~ ^[Yy]$ ]]; then
      info "Installing libmagic..."
      eval "$instal_libmagic_cmd" || fatal "Failed to install libmagic."
    else
      fatal "libmagic is required. Please install it and retry."
    fi
  else
    info "libmagic is already installed."
  fi
}

# installs Python packages that are not part of the standard poetry dependencies
install_python_extras() {
  info "Installing playwright chromium..."
  playwright install chromium || fatal "Failed to install playwright chromium"

  info "Installing browser-use..."
  uv tool install --force "git+https://github.com/chat2graph/browser-use.git@main#egg=browser-use[cli]" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host github.com || fatal "Failed to install browser-use"
}

# TODO: resolve dependency conflict resolution
# temporary workaround for aiohttp version conflicts until proper resolution in pyproject.toml
handle_dependency_conflicts() {
  #TODO: Remove this workaround after pyproject.toml can resolve the conflict

  # Force reinstall specific aiohttp version while downgrading ERROR messages to WARNING
  # Design Principles:
  # 1. Preserve full installation output (no information hidden)
  # 2. Convert ERROR to WARNING to prevent misleading appearance of failure
  info "Resolving aiohttp version conflict..."
  local target_aiohttp_version="3.12.13"
  pip install --force-reinstall "aiohttp==$target_aiohttp_version" --trusted-host pypi.org --trusted-host files.pythonhosted.org 2>&1 | sed 's/ERROR/WARNING/g'
}

build_python() {
  app_dir=$1

  cd ${app_dir}
  info "Installing python packages: ${app_dir}"
  poetry lock && poetry install || fatal "Failed to install python packages"
  install_python_extras
  handle_dependency_conflicts
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
