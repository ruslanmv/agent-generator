# install_python.sh
#!/usr/bin/env bash
set -euo pipefail

# Python installer for Ubuntu/Debian, macOS, and Windows (3.11–3.13)
# Detects OS, prompts for version, installs and configures the chosen Python3 as default on Ubuntu via update-alternatives.

print_header() { printf "\n==== %s ====\n\n" "$1"; }

prompt_menu() {
    local prompt="$1"; shift
    local options=("$@")
    PS3="$prompt "
    select opt in "${options[@]}"; do
        [[ -n "$opt" ]] && { echo "$opt"; return; } || echo "Invalid choice, try again." >&2
    done
}

# --- Detect operating system ---
OS_TYPE="unknown"
if [[ "$OSTYPE" == linux-gnu* ]]; then
    if [[ -f /etc/os-release ]]; then source /etc/os-release; fi
    case "$ID" in
        ubuntu|debian)
            OS_TYPE="ubuntu";;
        *) echo "❌ Unsupported Linux distribution: $ID" >&2; exit 1;;
    esac
elif [[ "$OSTYPE" == darwin* ]]; then
    OS_TYPE="macos"
elif [[ "$OSTYPE" == msys* || "$OSTYPE" == cygwin* || "$OSTYPE" == win32* ]]; then
    OS_TYPE="windows"
else
    echo "❌ Cannot detect or unsupported OS: $OSTYPE" >&2; exit 1
fi

print_header "Detected OS: $OS_TYPE"

# --- Python version selection ---
print_header "Select Python version to install"
PYVER=$(prompt_menu "Choose version (number):" "3.11" "3.12" "3.13")

# --- Ubuntu/Debian installer ---
install_ubuntu() {
    print_header "Ubuntu/Debian: Installing and configuring Python $PYVER as default"
    # Ensure pythonX.Y is installed
    if ! command -v python${PYVER} &>/dev/null; then
        echo "🚀 Installing python$PYVER..."
        sudo apt update
        sudo apt install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt update
        sudo apt install -y python${PYVER} python${PYVER}-venv python${PYVER}-dev
        echo "🎉 Installed python${PYVER}."
    else
        echo "✅ python${PYVER} already installed: $(python${PYVER} --version)"
    fi

    # Register both system python3 and pythonX.Y with update-alternatives
    echo "🚀 Registering python interpreters with update-alternatives..."
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYVER} 2

    # Let user pick the default
    echo "🚀 Launching selection menu to choose default python3..."
    sudo update-alternatives --config python3

    # Optionally register python -> python3
    echo "ℹ️ To make 'python' command point to the chosen python3, register it as well?"
    read -p "Create python alternative? (y/N): " RESP
    if [[ "$RESP" =~ ^[Yy] ]]; then
        sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
        sudo update-alternatives --config python
    fi

    echo "🎉 Default python3 now -> $(python3 --version)"
}

# --- macOS installer ---
install_macos() {
    print_header "macOS: Installing Python $PYVER"
    command_exists() { command -v "$1" &>/dev/null; }
    if ! command_exists brew; then
        echo "🚀 Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(brew shellenv)"
    fi
    echo "🚀 Updating Homebrew..."
    brew update
    short=${PYVER%.*}
    if brew list python@${short} &>/dev/null; then
        echo "✅ python@${short} already installed: $(python${short} --version)"
    else
        echo "🚀 Installing python@${short}..."
        brew install python@${short}
        echo "🎉 Installed python@${short}."
    fi
    echo "🚀 Linking python@${short} as default python3..."
    brew link --force --overwrite python@${short}
    echo "🎉 Default python3 -> $(python3 --version)"
}

# --- Windows installer (winget) ---
install_windows() {
    print_header "Windows: Installing Python $PYVER"
    if ! command -v winget &>/dev/null; then
        echo "❌ winget not found. Please install App Installer." >&2; exit 1
    fi
    WID="Python.Python.${PYVER//./}"
    if winget list --id "$WID" &>/dev/null; then
        echo "✅ $WID already installed"
    else
        echo "🚀 Installing $WID..."
        winget install --silent --accept-package-agreements --accept-source-agreements "$WID"
        echo "🎉 Installed $WID."
    fi
    echo "ℹ️ Use 'py -${PYVER}' or adjust your user PATH to preference without changing system defaults."
}

# --- Dispatch installation ---
case "$OS_TYPE" in
    ubuntu)  install_ubuntu  ;;
    macos)   install_macos   ;;
    windows) install_windows ;;
    *)       echo "Unsupported OS for this installer."; exit 1;;
esac

exit 0
