#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
CrossPlatform/.venv/bin/python CrossPlatform/main.py
