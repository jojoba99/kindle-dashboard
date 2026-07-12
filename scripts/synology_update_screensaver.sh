#!/bin/sh
set -eu

cd /volume1/web/kindle-dashboard

if command -v python3 >/dev/null 2>&1; then
  PY=python3
elif [ -x /usr/local/bin/python3 ]; then
  PY=/usr/local/bin/python3
else
  echo "python3 not found. Install Python 3 from Synology Package Center." >&2
  exit 1
fi

$PY scripts/update_data.py
$PY scripts/render_screensaver.py
