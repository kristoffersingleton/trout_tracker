#!/usr/bin/env bash
cd "$(dirname "$0")"
.venv/bin/python find_stocked.py | tee /dev/tty | clip.exe
