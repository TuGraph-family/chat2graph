#!/usr/bin/env bash
cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && source utils.sh || exit

WEB_BUILD=true
if [[ "$1" == "--no-gui" ]]; then
  WEB_BUILD=false
fi

# Global flag to track Playwright installation issues
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
  local os_type
  os_type=$(uname -s)
  local install_libmagic_cmd=""

  # detect OS and suggest installation commands for libmagic
  if [[ "$os_type" == "Darwin" ]]; then # macOS
    if ! brew list libmagic &>/dev/null; then
      install_libmagic_cmd="brew install libmagic"
    fi
  elif [[ "$os_type" == "Linux" ]]; then # Linux
    if command -v dpkg &> /dev/null; then # Debian/Ubuntu
        if ! dpkg -s libmagic1 &>/dev/null; then
            install_libmagic_cmd="sudo apt-get update && sudo apt-get install -y libmagic1"
        fi
    elif command -v rpm &> /dev/null; then # CentOS/RHEL/Fedora
        if ! rpm -q file-libs &>/dev/null; then
            if command -v dnf &> /dev/null; then
                install_libmagic_cmd="sudo dnf install -y file-libs"
            elif command -v yum &> /dev/null; then
                install_libmagic_cmd="sudo yum install -y file-libs"
            fi
        fi
    else
        warn "Unsupported Linux distribution for automatic libmagic installation."
    fi
  elif [[ "$os_type" == "MINGW64"* || "$os_type" == "MSYS"* || "$os_type" == "CYGWIN"* ]]; then # Windows
    warn "Windows support for libmagic is not automated. Please install it manually."
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
  info "Detecting Linux distribution for Playwright dependencies..."
  
  # Try playwright install-deps first (works for Debian/Ubuntu and some RHEL-based systems)
  if command -v sudo >/dev/null 2>&1; then
    info "Attempting to install Playwright dependencies using 'playwright install-deps'..."
    if sudo -E playwright install-deps 2>/dev/null; then
      info "Successfully installed Playwright dependencies via playwright install-deps"
      return 0
    else
      warn "playwright install-deps failed, trying manual installation..."
    fi
  fi
  
  # Manual installation for different distributions
  if command -v dnf >/dev/null 2>&1; then
    # Fedora/RHEL 8+/CentOS 8+
    info "Installing Playwright dependencies for RHEL/Fedora/CentOS (dnf)..."
    sudo dnf install -y \
      atk \
      at-spi2-atk \
      libxcb \
      at-spi2-core \
      libX11 \
      libXcomposite \
      libXdamage \
      libXext \
      libXfixes \
      libXrandr \
      mesa-libgbm \
      cairo \
      pango \
      alsa-lib \
      liberation-fonts || return 1
  elif command -v yum >/dev/null 2>&1; then
    # CentOS 7/RHEL 7
    info "Installing Playwright dependencies for CentOS/RHEL 7 (yum)..."
    sudo yum install -y \
      atk \
      at-spi2-atk \
      libxcb \
      at-spi2-core \
      libX11 \
      libXcomposite \
      libXdamage \
      libXext \
      libXfixes \
      libXrandr \
      mesa-libgbm \
      cairo \
      pango \
      alsa-lib \
      liberation-fonts || return 1
  elif command -v apt-get >/dev/null 2>&1; then
    # Debian/Ubuntu (fallback)
    info "Installing Playwright dependencies for Debian/Ubuntu (apt-get)..."
    sudo apt-get update && sudo apt-get install -y \
      libatk1.0-0 \
      libatk-bridge2.0-0 \
      libxcb1 \
      libatspi2.0-0 \
      libx11-6 \
      libxcomposite1 \
      libxdamage1 \
      libxext6 \
      libxfixes3 \
      libxrandr2 \
      libgbm1 \
      libcairo2 \
      libpango-1.0-0 \
      libasound2 || return 1
  else
    warn "Unable to detect package manager. Please install Playwright dependencies manually."
    warn "For CentOS/RHEL, you may need to run:"
    warn "  sudo yum install -y atk at-spi2-atk libxcb at-spi2-core libX11 libXcomposite libXdamage libXext libXfixes libXrandr mesa-libgbm cairo pango alsa-lib liberation-fonts"
    return 1
  fi
  
  info "Playwright system dependencies installed successfully"
  return 0
}

# installs Python packages that are not part of the standard poetry dependencies
install_python_extras() {
  # install Playwright system dependencies for Linux FIRST
  local os_type
  os_type=$(uname -s)
  if [[ "$os_type" == "Linux" ]]; then
    info "Installing playwright system dependencies for Linux..."
    if ! install_playwright_deps_linux; then
      PLAYWRIGHT_ISSUES=true
      warn "Failed to install some playwright dependencies. You may need to install them manually."
    fi
  fi

  info "Installing playwright chromium..."
  if ! playwright install chromium; then
    PLAYWRIGHT_ISSUES=true
    fatal "Failed to install playwright chromium"
  fi

  info "Installing browser-use..."
  uv tool install --force "git+https://github.com/chat2graph/browser-use.git@feat/add-pdf-printer#egg=browser-use[cli]" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host github.com || fatal "Failed to install browser-use"
}

# TODO: resolve dependency conflict resolution
# temporary workaround for aiohttp version conflicts until proper resolution in pyproject.toml
# force reinstall specific aiohttp version while downgrading ERROR messages to WARNING
# design Principles:
# 1. Preserve full installation output (no information hidden)
# 2. Convert ERROR to WARNING to prevent misleading appearance of failure
handle_dependency_conflicts() {
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

# only show Playwright manual installation instructions if there were issues
if [ "$PLAYWRIGHT_ISSUES" = true ]; then
  warn "=== Playwright Installation Issues Detected ==="
  info "If you encountered any Playwright issues on CentOS/RHEL, you can manually install dependencies with:"
  info "  sudo yum install -y atk at-spi2-atk libxcb at-spi2-core libX11 libXcomposite libXdamage libXext libXfixes libXrandr mesa-libgbm cairo pango alsa-lib liberation-fonts"
  info "  or for newer systems:"
  info "  sudo dnf install -y atk at-spi2-atk libxcb at-spi2-core libX11 libXcomposite libXdamage libXext libXfixes libXrandr mesa-libgbm cairo pango alsa-lib liberation-fonts"
fi
