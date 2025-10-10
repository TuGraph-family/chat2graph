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
  # check for poetry. if missing, show a help message and exit
  if ! command -v poetry >/dev/null 2>&1; then
    echo -n "poetry is not installed. Do you want to install it now? (y/n): "
    read -r _response_poetry
    if [[ "$_response_poetry" =~ ^[Yy]$ ]]; then
      info "Installing poetry via pip install poetry..."
      if pip install poetry; then
        info "poetry installed successfully."
      else
        echo
        echo "Automatic installation failed. You can run the following command manually and retry:"
        echo "pip install poetry"
        echo
        fatal "Failed to install poetry automatically."
      fi
    else
      fatal "poetry is required. Please install it and retry."
    fi
  fi
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

# hard-coded fixes for Alibaba Cloud Linux
install_alinux_browsers() {
  info "Applying Alibaba Cloud Linux specific browser fixes..."

  # set up environment variables for alinux
  export PLAYWRIGHT_BROWSERS_PATH="/opt/playwright"

  # create necessary directories
  if ! sudo mkdir -p /opt/playwright; then
    warn "Failed to create /opt/playwright directory"
    return 1
  fi

  sudo chown -R $(whoami):$(whoami) /opt/playwright 2>/dev/null || true

  # check if wget and unzip are available
  if ! command -v wget >/dev/null 2>&1; then
    warn "wget not found, installing..."
    sudo yum install -y wget >/dev/null 2>&1 || return 1
  fi

  if ! command -v unzip >/dev/null 2>&1; then
    warn "unzip not found, installing..."
    sudo yum install -y unzip >/dev/null 2>&1 || return 1
  fi

  # try to download chromium directly
  local chromium_url="https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/1097615/chrome-linux.zip"
  local temp_dir="/tmp/playwright-chromium"
  local chrome_install_dir="/opt/playwright/chromium"

  info "    Attempting to download Chromium directly for alinux..."

  # clean up any existing temp directory
  rm -rf "$temp_dir"
  mkdir -p "$temp_dir"

  info "    Downloading Chromium from $chromium_url..."
  if wget --timeout=30 --tries=3 -O "$temp_dir/chrome-linux.zip" "$chromium_url"; then
    info "    Download completed, extracting..."
    local original_dir=$(pwd)
    cd "$temp_dir"
    if unzip -q chrome-linux.zip; then
      info "    Extraction completed, installing to $chrome_install_dir..."
      if sudo mkdir -p "$chrome_install_dir" && \
         sudo cp -r chrome-linux/* "$chrome_install_dir/" && \
         sudo chmod +x "$chrome_install_dir/chrome"; then
        
        # Create symbolic links for Playwright and system compatibility
        info "    Creating symbolic links for browser compatibility..."
        sudo mkdir -p /opt/google/chrome
        sudo ln -sf "$chrome_install_dir/chrome" /opt/google/chrome/chrome
        sudo ln -sf "$chrome_install_dir/chrome" /usr/bin/chromium 2>/dev/null || true
        sudo ln -sf "$chrome_install_dir/chrome" /usr/bin/google-chrome 2>/dev/null || true
        
        info "    Successfully installed Chromium manually for alinux"
        cd "$original_dir"
        rm -rf "$temp_dir"
        return 0
      else
        warn "Failed to copy or set permissions for Chromium"
      fi
    else
      warn "Failed to extract Chromium archive"
    fi
    cd "$original_dir"
  else
    warn "Failed to download Chromium from $chromium_url"
  fi
  
  rm -rf "$temp_dir"
  return 1
}

# install Playwright system dependencies for Linux distributions
install_playwright_deps_linux() {
  info "Installing Playwright system dependencies for Linux..."

  # skip playwright install-deps for unsupported distributions like alinux
  local distro_id=""
  if [[ -f /etc/os-release ]]; then
    distro_id=$(bash -c 'source /etc/os-release && echo $ID')
  fi
  
  # hard-coded solution for Alibaba Cloud Linux (alinux)
  if [[ "$distro_id" == "alinux" ]]; then
    info "    Detected Alibaba Cloud Linux - applying hardcoded fixes"
    
    # install essential packages for alinux
    if command -v yum >/dev/null 2>&1; then
      sudo yum install -y \
        nss \
        atk \
        at-spi2-atk \
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
        liberation-fonts \
        libXScrnSaver \
        gtk3 \
        libdrm \
        libxkbcommon \
        libxss \
        glib2 >/dev/null 2>&1
      
      info "    Installed alinux-specific dependencies"
    fi
    return 0
  fi
  
  # only use playwright install-deps for supported distributions
  if [[ "$distro_id" == "ubuntu" || "$distro_id" == "debian" ]]; then
    if command -v sudo >/dev/null 2>&1 && playwright install-deps >/dev/null 2>&1; then
      info "    Successfully installed Playwright dependencies via playwright install-deps"
      return 0
    fi
  else
    info "    Detected $distro_id - using manual dependency installation"
  fi

  # Manual installation for all other distributions
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
  local work_dir=$(pwd)

  # install Playwright system dependencies for Linux only
  if [[ "$os_type" == "Linux" ]]; then
    if ! install_playwright_deps_linux; then
      PLAYWRIGHT_ISSUES=true
      warn "Failed to install some playwright dependencies. You may need to install them manually."
    fi
  fi

  info "Installing playwright browsers..."
  
  # hard-coded solution for Alibaba Cloud Linux (alinux)
  local distro_id=""
  if [[ -f /etc/os-release ]]; then
    distro_id=$(bash -c 'source /etc/os-release && echo $ID')
  fi
  
  if [[ "$distro_id" == "alinux" ]]; then
    info "    Applying alinux-specific browser installation..."

    # for alinux, use our custom installation method directly
    if install_alinux_browsers; then
      info "    Successfully installed browsers using alinux-specific method"
    elif command -v chromium-browser >/dev/null 2>&1; then
      info "    Using system chromium-browser as fallback"
    elif command -v google-chrome >/dev/null 2>&1; then
      info "    Using system google-chrome as fallback"
    else
      PLAYWRIGHT_ISSUES=true
      warn "Failed to install Playwright browsers on alinux. Manual installation may be required."
    fi
  else
    # standard installation for other distributions
    if python -m playwright install chromium >/dev/null 2>&1; then
      info "    Successfully installed Playwright Chromium via Python"
    elif playwright install chromium >/dev/null 2>&1; then
      info "    Successfully installed Playwright Chromium"
    else
      PLAYWRIGHT_ISSUES=true
      warn "Failed to install Playwright Chromium. You may need to install it manually."
    fi
  fi

  info "Installing browser-use..."
  uv tool install --force "git+https://github.com/chat2graph/browser-use.git@feat/add-pdf-printer#egg=browser-use[cli]" --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host github.com || fatal "Failed to install browser-use"
}

# TODO: resolve dependency conflict resolution
# temporary workaround for aiohttp version conflicts until proper resolution in pyproject.toml
# force reinstall specific aiohttp version without showing installation output
handle_dependency_conflicts() {
  info "Resolving aiohttp version conflict..."
  pip install --force-reinstall "aiohttp==3.12.13" --trusted-host pypi.org --trusted-host files.pythonhosted.org 2>&1 | sed 's/ERROR/WARNING/g'
  # install memfuse (^0.3.2)
  info "Resolved memfuse dependency..."
  pip install --force-reinstall "memfuse>=0.3.2" --trusted-host pypi.org --trusted-host files.pythonhosted.org 2>&1 | sed 's/ERROR/WARNING/g'
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

info "=== Chat2Graph Build Process Started ==="
info "Build configuration: WEB_BUILD=$WEB_BUILD"

check_env
build_python $project_root
if [ "$WEB_BUILD" = true ]; then
  build_web $project_root
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
