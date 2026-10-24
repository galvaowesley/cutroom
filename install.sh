#!/usr/bin/env sh
# Linux and macOS wrapper for install.py (the cross-platform installer). Same options:
#   ./install.sh [--agent claude,codex] [--home ~/Documents/cutroom] [--output DIR] [--language pt-BR] [--uninstall]
set -e
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 2; }
exec python3 install.py "$@"
