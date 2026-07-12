#!/bin/sh
set -eu

URL="${1:-http://172.22.22.116/kindle-dashboard/screensaver/kindle-dashboard.png}"
TARGET="/mnt/us/linkss/screensavers/bg_medium_ss00.png"
TMP="/mnt/us/linkss/screensavers/.kindle-dashboard.tmp.png"
LOG="/mnt/us/linkss/kindle-dashboard-update.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') updating from ${URL}" >> "${LOG}"

if command -v wget >/dev/null 2>&1; then
  wget -q -O "${TMP}" "${URL}"
elif command -v curl >/dev/null 2>&1; then
  curl -fsSL "${URL}" -o "${TMP}"
else
  echo "no wget or curl found" >> "${LOG}"
  exit 1
fi

if [ ! -s "${TMP}" ]; then
  echo "downloaded file is empty" >> "${LOG}"
  rm -f "${TMP}"
  exit 1
fi

mv "${TMP}" "${TARGET}"
sync

echo "$(date '+%Y-%m-%d %H:%M:%S') updated ${TARGET}" >> "${LOG}"

if command -v eips >/dev/null 2>&1; then
  eips 0 39 "Kindle dashboard updated"
fi
