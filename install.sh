#!/bin/bash
#
# c0admin universal installer
# Supports: Debian/Ubuntu, Fedora/RHEL/CentOS, Arch/Manjaro, openSUSE, Alpine, macOS
#
set -e

INSTALL_DIR="$HOME/.c0admin"
EXECUTABLE_NAME="c0admin"
LAUNCHER_PATH="/usr/local/bin/$EXECUTABLE_NAME"
REPO_URL="https://github.com/ufuayk/c0admin.git"

# ---------- helpers ----------
info()  { echo -e "\033[1;34m[*]\033[0m $1"; }
ok()    { echo -e "\033[1;32m[+]\033[0m $1"; }
warn()  { echo -e "\033[1;33m[!]\033[0m $1"; }
err()   { echo -e "\033[1;31m[x]\033[0m $1" >&2; }

need_sudo() {
    # macOS Homebrew calls should NOT run as root
    if [ "$OS" = "macos" ]; then
        "$@"
    else
        if [ "$(id -u)" -eq 0 ]; then
            "$@"
        else
            sudo "$@"
        fi
    fi
}

# ---------- OS / package manager detection ----------
detect_os() {
    case "$(uname -s)" in
        Darwin)
            OS="macos"
            PKG_MANAGER="brew"
            ;;
        Linux)
            OS="linux"
            if [ -f /etc/os-release ]; then
                . /etc/os-release
                DISTRO_ID="${ID:-unknown}"
                DISTRO_ID_LIKE="${ID_LIKE:-}"
            else
                DISTRO_ID="unknown"
                DISTRO_ID_LIKE=""
            fi

            if command -v apt-get >/dev/null 2>&1; then
                PKG_MANAGER="apt"
            elif command -v dnf >/dev/null 2>&1; then
                PKG_MANAGER="dnf"
            elif command -v yum >/dev/null 2>&1; then
                PKG_MANAGER="yum"
            elif command -v pacman >/dev/null 2>&1; then
                PKG_MANAGER="pacman"
            elif command -v zypper >/dev/null 2>&1; then
                PKG_MANAGER="zypper"
            elif command -v apk >/dev/null 2>&1; then
                PKG_MANAGER="apk"
            else
                PKG_MANAGER="unknown"
            fi
            ;;
        *)
            err "Unsupported operating system: $(uname -s)"
            exit 1
            ;;
    esac
}

# ---------- dependency installation ----------
install_dependencies() {
    info "Installing system dependencies (python3, venv, pip, git)..."

    case "$PKG_MANAGER" in
        apt)
            need_sudo apt-get update -y
            need_sudo apt-get install -y python3 python3-venv python3-pip git
            ;;
        dnf)
            need_sudo dnf install -y python3 python3-pip git
            ;;
        yum)
            need_sudo yum install -y python3 python3-pip git
            ;;
        pacman)
            need_sudo pacman -Sy --noconfirm python python-pip git
            ;;
        zypper)
            need_sudo zypper --non-interactive install python3 python3-pip git
            ;;
        apk)
            need_sudo apk add --no-cache python3 py3-pip git
            ;;
        brew)
            if ! command -v brew >/dev/null 2>&1; then
                warn "Homebrew not found. Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                # make sure brew is on PATH for the rest of this script (Apple Silicon default)
                if [ -x /opt/homebrew/bin/brew ]; then
                    eval "$(/opt/homebrew/bin/brew shellenv)"
                elif [ -x /usr/local/bin/brew ]; then
                    eval "$(/usr/local/bin/brew shellenv)"
                fi
            fi
            brew install git || true
            # Pin to Python 3.12: some pinned deps in requirements.txt (e.g. pydantic_core)
            # don't have prebuilt wheels yet for the very latest CPython (e.g. 3.14),
            # which forces a source/Rust build that fails on most machines.
            brew install python@3.12 || true
            ;;
        unknown)
            err "Could not detect a supported package manager."
            err "Please install python3, python3-venv, python3-pip and git manually, then re-run this script."
            exit 1
            ;;
    esac

    ok "System dependencies installed."
}

# ---------- python binary detection ----------
detect_python() {
    # On macOS prefer the pinned python@3.12 from Homebrew, since some pinned
    # dependencies (e.g. pydantic_core) don't yet ship wheels for the newest
    # CPython and fail to build from source.
    if [ "$OS" = "macos" ]; then
        for candidate in \
            "/opt/homebrew/opt/python@3.12/bin/python3.12" \
            "/usr/local/opt/python@3.12/bin/python3.12"; do
            if [ -x "$candidate" ]; then
                PYTHON_BIN="$candidate"
                return
            fi
        done
        if command -v python3.12 >/dev/null 2>&1; then
            PYTHON_BIN="python3.12"
            return
        fi
        warn "python@3.12 not found, falling back to default python3 (may be too new for some dependencies)."
    fi

    if command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    elif command -v python >/dev/null 2>&1; then
        PYTHON_BIN="python"
    else
        err "python3 could not be found after installation. Aborting."
        exit 1
    fi
}

# ---------- main install ----------
main() {
    echo "======================================="
    echo "        c0admin universal installer"
    echo "======================================="

    detect_os
    info "Detected OS: $OS${DISTRO_ID:+ ($DISTRO_ID)} — package manager: $PKG_MANAGER"

    install_dependencies
    detect_python

    if [ -d "$INSTALL_DIR" ]; then
        warn "Previous installation found at $INSTALL_DIR. Removing..."
        rm -rf "$INSTALL_DIR"
    fi

    info "Downloading GitHub repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"

    info "Creating Python virtual environment..."
    "$PYTHON_BIN" -m venv "$INSTALL_DIR/venv"

    info "Installing Python packages..."
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip >/dev/null
    "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

    info "Setting up '$EXECUTABLE_NAME' command..."

    LAUNCHER_CONTENT="#!/bin/bash
\"$INSTALL_DIR/venv/bin/python3\" \"$INSTALL_DIR/main.py\" \"\$@\"
"

    if [ -w "$(dirname "$LAUNCHER_PATH")" ]; then
        printf '%s' "$LAUNCHER_CONTENT" > "$LAUNCHER_PATH"
    else
        need_sudo bash -c "cat > '$LAUNCHER_PATH'" <<< "$LAUNCHER_CONTENT"
    fi
    need_sudo chmod +x "$LAUNCHER_PATH"

    ok "Installation completed!"
    echo
    echo "You can run the application by typing '$EXECUTABLE_NAME' in your terminal."
}

main "$@"
