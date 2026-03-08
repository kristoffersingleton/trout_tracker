#!/usr/bin/env bash
cd "$(dirname "$0")"
python3 find_stocked.py | tee /dev/tty | clip.exe
