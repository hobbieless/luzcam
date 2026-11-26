#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
TASK_PYTHON=""
for candidate in python3.12; do
 if command -v "$candidate" >/dev/null 2>&1; then
  if "$candidate" -c 'import sys; raise SystemExit(not ((3,12)<=sys.version_info[:2]<=(3,13)))'; then TASK_PYTHON="$candidate"; break; fi
 fi
done
if [ -z "$TASK_PYTHON" ]; then echo 'Instala Python 3.12 desde python.org para usar el perfil Qt 6.8.3.'; exit 1; fi
"$TASK_PYTHON" -m venv CrossPlatform/.venv
CrossPlatform/.venv/bin/python -m pip install -r CrossPlatform/requirements-macos12.txt
CrossPlatform/.venv/bin/python Tests/portable-model.py
