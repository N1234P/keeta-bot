#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1

python3 ./keeta-raid-bot/main.py &
python3 ./keeta-whale-bot/main.py &


wait