#!/bin/sh
# macOS package of the same shared app used by build.cmd on Windows.
set -eu
cd "$(dirname "$0")"
if [ ! -x CrossPlatform/.venv/bin/python ]; then
  sh CrossPlatform/setup-mac.sh
fi
CrossPlatform/.venv/bin/python -m pip install -r CrossPlatform/requirements-build.txt
CrossPlatform/.venv/bin/python CrossPlatform/build-desktop.py
