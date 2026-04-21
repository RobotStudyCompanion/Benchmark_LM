#!/usr/bin/env bash
# setup.sh — environment management for Benchmarking_LLM (Linux only).
#
# Usage:
#   ./setup.sh            install (creates .venv and installs requirements)
#   ./setup.sh --force    recreate .venv from scratch
#   ./setup.sh --clean    remove .venv and exit
#   ./setup.sh --help     show this message
#
# After install, activate with:  source .venv/bin/activate

set -euo pipefail

# --- Move to script directory so relative paths work regardless of cwd ---
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"
ASSUME_YES=0

VENV_DIR=".venv"
REQ_FILE="requirements.txt"
PYTHON_MIN="3.8"

# --- Helpers -----------------------------------------------------------------
log()  { printf '\033[1;34m[setup]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn ]\033[0m %s\n' "$*"; }
err()  { printf '\033[1;31m[err  ]\033[0m %s\n' "$*" >&2; }

usage() {
    cat <<'EOF'
setup.sh — environment management for Benchmarking_LLM (Linux only).

Usage:
  ./setup.sh            install (creates .venv and installs requirements)
  ./setup.sh --force    recreate .venv from scratch
  ./setup.sh --clean    remove .venv and exit
  ./setup.sh --yes      non-interactive install (answers yes to prompts)
  ./setup.sh --help     show this message

After install, activate with:  source .venv/bin/activate
EOF
    exit 0
}
confirm() {
    [[ "$ASSUME_YES" == "1" ]] && return 0
    local reply
    read -r -p "$1 [y/N] " reply
    [[ "$reply" =~ ^[Yy]$ ]]
}

cleanup_on_interrupt() {
    warn "Interrupted. Partial venv may be left at $VENV_DIR — rerun with --force to recreate."
    exit 130
}
trap cleanup_on_interrupt INT TERM

# --- OS check ---------------------------------------------------------------
if [[ "$(uname -s)" != "Linux" ]]; then
    err "This setup script supports Linux only. Detected: $(uname -s)"
    exit 1
fi

# --- Parse args -------------------------------------------------------------
MODE="install"
case "${1:-}" in
    --help|-h)   usage ;;
    --clean)     MODE="clean" ;;
    --force)     MODE="force" ;;
     --yes|-y)    ASSUME_YES=1; MODE="install" ;;
    "")          MODE="install" ;;
    *)           err "Unknown option: $1"; usage ;;
esac

# --- Clean mode -------------------------------------------------------------
if [[ "$MODE" == "clean" ]]; then
    if [[ -d "$VENV_DIR" ]]; then
        log "Removing $VENV_DIR ..."
        rm -rf "$VENV_DIR"
        log "Done."
    else
        log "No $VENV_DIR to clean."
    fi
    exit 0
fi

# --- Python check -----------------------------------------------------------
if ! command -v python3 &>/dev/null; then
    err "python3 not found on PATH."
    exit 1
fi

PY_VER="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
log "Found python3 ($PY_VER)"

if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    err "Python >= $PYTHON_MIN required, found $PY_VER"
    exit 1
fi

if ! python3 -c "import venv" &>/dev/null; then
    err "python3-venv missing. Install with: sudo apt install python3-venv"
    exit 1
fi

# --- Handle existing venv ---------------------------------------------------
if [[ -d "$VENV_DIR" ]]; then
    if [[ "$MODE" == "force" ]]; then
        log "Removing existing $VENV_DIR (--force)"
        rm -rf "$VENV_DIR"
    else
        warn "$VENV_DIR already exists."
        if confirm "Recreate it from scratch?"; then
            rm -rf "$VENV_DIR"
        else
            log "Keeping existing venv; will reinstall requirements into it."
        fi
    fi
fi

# --- Create venv if needed --------------------------------------------------
if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating venv at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# --- Activate and install ---------------------------------------------------
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

if [[ "${VIRTUAL_ENV:-}" != "$SCRIPT_DIR/$VENV_DIR" ]]; then
    err "venv activation failed (VIRTUAL_ENV=${VIRTUAL_ENV:-unset})"
    exit 1
fi

log "Upgrading pip ..."
python -m pip install --upgrade pip --quiet

if [[ ! -f "$REQ_FILE" ]]; then
    err "$REQ_FILE not found in $SCRIPT_DIR"
    exit 1
fi

log "Installing from $REQ_FILE ..."
python -m pip install --upgrade -r "$REQ_FILE"

# --- Optional Ollama check --------------------------------------------------
if ! command -v ollama &>/dev/null; then
    warn "ollama CLI not found on PATH."
    warn "The Python bindings are installed, but the benchmark scripts require"
    warn "a running Ollama daemon. Install from: https://ollama.com/download"
fi

# --- Done -------------------------------------------------------------------
log "Setup complete."
log ""
log "Activate the environment with:"
log "    source $VENV_DIR/bin/activate"
log ""
log "Verify the install with:"
log "    python -m py_compile *.py && echo OK"