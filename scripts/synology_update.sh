#!/bin/sh
set -eu

cd /volume1/web/kindle-dashboard

if command -v python3 >/dev/null 2>&1; then
  python3 scripts/update_data.py
elif [ -x /usr/local/bin/python3 ]; then
  /usr/local/bin/python3 scripts/update_data.py
else
  echo "python3 not found. Install Python 3 from Synology Package Center." >&2
  exit 1
fi
