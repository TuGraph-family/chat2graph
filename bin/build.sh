#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && source utils.sh || exit

WEB_BUILD=true
if [[ "$1" == "--no-gui" ]]; then
  WEB_BUILD=false
fi

# global flag to track Playwright installation issues
PLAYWRIGHT_ISSUES=false

check_env() {
  info "Checking environment:"
  info "    Operating System: $(uname -s) $(uname -r)"
  info "    Architecture: $(uname -m)"

  check_command python 2 || fatal
  python -c 'import sys; exit(0 if (3, 10) <= sys.version_info < (3, 12) else 1)' \
    || fatal "Python version must be >=3.10 and <3.12. Found $(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
  check_command pip 2 || fatal
  check_command poetry 3 ' |)' || fatal "Run with 'pip install poetry' and retry."
  check_command node 2 'v' || fatal
  check_command npm || fatal

  info "Checking for libmagic..."
  local os_type=$(uname -s)
  local install_libmagic_cmd=""

  # Simplified OS detection for libmagic
  if [[ "$os_type" == "Darwin" ]]; then # macOS
    if command -v brew >/dev/null 2>&1 && ! brew list libmagic &>/dev/null; then
      install_libmagic_cmd="brew install libmagic"
    fi
  elif [[ "$os_type" == "Linux" ]]; then # Linux
    if command -v apt-get &> /dev/null && ! dpkg -s libmagic1 &>/dev/null; then
      install_libmagic_cmd="sudo apt-get update && sudo apt-get install -y libmagic1"
    elif command -v yum &> /dev/null && ! rpm -q file-libs &>/dev/null; then
      install_libmagic_cmd="sudo yum install -y file-libs"
    elif command -v dnf &> /dev/null && ! rpm -q file-libs &>/dev/null; then
      install_libmagic_cmd="sudo dnf install -y file-libs"
    fi
  fi

  if [[ -n "$install_libmagic_cmd" ]]; then
    echo -n "libmagic is not found. Do you want to install it now? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
      info "Installing libmagic..."
      eval "$install_libmagic_cmd" || fatal "Failed to install libmagic."
    else
      fatal "libmagic is required. Please install it and retry."
    fi
  else
    info "libmagic is already installed."
  fi
}

# install Playwright system dependencies for Linux distributions
install_playwright_deps_linux() {
  info "Installing Playwright system dependencies for Linux..."

  # skip playwright install-deps for unsupported distributions like alinux
  local distro_id=""
  if [[ -f /etc/os-release ]]; then
    distro_id=$(bash -c 'source /etc/os-release && echo $ID')
  fi
  
  # only use playwright install-deps for supported distributions
  if [[ "$distro_id" == "ubuntu" || "$distro_id" == "debian" ]]; then
    if command -v sudo >/dev/null 2>&1 && playwright install-deps >/dev/null 2>&1; then
      info "Successfully installed Playwright dependencies via playwright install-deps"
      return 0
    fi
  else
    info "Detected $distro_id - using manual dependency installation"
  fi

  # manual installation for all distributions
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update >/dev/null 2>&1
    sudo apt-get install -y libnss3 libatk-bridge2.0-0 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2 >/dev/null 2>&1
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y nss atk at-spi2-atk libX11 libXcomposite libXdamage libXrandr mesa-libgbm libxss1 alsa-lib >/dev/null 2>&1
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y nss atk at-spi2-atk libX11 libXcomposite libXdamage libXrandr mesa-libgbm libxss1 alsa-lib >/dev/null 2>&1
  fi

  return 0
}

# installs Python packages that are not part of the standard poetry dependencies
install_python_extras() {
  local os_type=$(uname -s)

  # install Playwright system dependencies for Linux only
  if [[ "$os_type" == "Linux" ]]; then
    if ! install_playwright_deps_linux; then
      PLAYWRIGHT_ISSUES=true
      warn "Failed to install some playwright dependencies. You may need to install them manually."
    fi
  fi

  info "Installing playwright browsers..."
  # use Python playwright instead of npx for more reliable installation
  if python -m playwright install chromium >/dev/null 2>&1; then
    info "Successfully installed Playwright Chromium via Python"
  elif playwright install chromium >/dev/null 2>&1; then
    info "Successfully installed Playwright Chromium"
  else
    PLAYWRIGHT_ISSUES=true
    warn "Failed to install Playwright Chromium. You may need to install it manually."
  fi

  info "Installing browser-use..."
  uv tool install --force "git+https://github.com/chat2graph/browser-use.git@feat/add-pdf-printer#egg=browser-use[cli]" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host github.com || fatal "Failed to install browser-use"
}

# TODO: resolve dependency conflict resolution
# temporary workaround for aiohttp version conflicts until proper resolution in pyproject.toml
# force reinstall specific aiohttp version without showing installation output
handle_dependency_conflicts() {
  info "Resolving aiohttp version conflict..."
  local target_aiohttp_version="3.12.13"
  pip install --force-reinstall "aiohttp==$target_aiohttp_version" --trusted-host pypi.org --trusted-host files.pythonhosted.org >/dev/null 2>&1 || warn "Failed to resolve aiohttp version conflict"
}

build_python() {  
  app_dir=$1

  cd ${app_dir}
  info "Installing python packages: ${app_dir}"
  poetry lock && poetry install || fatal "Failed to install python packages"
  install_python_extras
  handle_dependency_conflicts
}

WEB_BUILD() {
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

info "=== Chat2Graph Build Process Started ==="
info "Build configuration: WEB_BUILD=$WEB_BUILD"

check_env
build_python $project_root
if [ "$WEB_BUILD" = true ]; then
  WEB_BUILD $project_root
fi

release_lock $lock_file

info "=== Build Completed Successfully ==="

# only show manual installation instructions if there were issues
if [ "$PLAYWRIGHT_ISSUES" = true ]; then
  warn "=== Playwright Installation Issues Detected ==="
  info "To resolve Playwright issues, try:"
  info "  playwright install chromium"
  info "  or visit: https://playwright.dev/docs/installation"
fi
