#!/usr/bin/env bash
set -euo pipefail

SYSINFO=/proc/sysinfo
BASE_URL="https://www.ibm.com/support/resourcelink/api/content/raw/hkd-public"

TYPE=$(awk -F: '/Type:/ {gsub(/ /,"",$2); print $2}' "$SYSINFO")
PLANT=$(awk -F: '/Plant:/ {gsub(/ /,"",$2); print $2}' "$SYSINFO")
SEQ=$(awk -F: '/Sequence Code:/ {gsub(/ /,"",$2); print $2}' "$SYSINFO")

# IBM only uses the last 5 hex chars of the sequence
SEQ_SHORT=${SEQ: -5}

FILENAME="HKD-${TYPE}-${PLANT}${SEQ_SHORT}.crt"
URL="${BASE_URL}/${FILENAME}"

echo "Login at https://www.ibm.com/support/resourcelink/ and then download:"
echo "$URL"

