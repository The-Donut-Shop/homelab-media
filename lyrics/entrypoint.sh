#!/bin/sh
# Every INTERVAL_SECONDS:
#   1. index new tracks in /music into the beets database (as-is: no autotag,
#      no copy, no move, no tag writes)
#   2. drop database entries for tracks that were deleted from disk
#   3. fetch synced lyrics for every track that has no .lrc yet
set -u
INTERVAL="${INTERVAL_SECONDS:-1800}"

while true; do
  echo "[$(date -Iseconds)] indexing /music"
  beet import -q -i -A -C -W /music >/dev/null 2>&1 || echo "  import: nothing new or error (see /config/import.log)"
  beet update >/dev/null 2>&1 || true
  echo "[$(date -Iseconds)] fetching missing lyrics"
  beet getlrc -q || echo "  getlrc returned an error"
  echo "[$(date -Iseconds)] sleeping ${INTERVAL}s"
  sleep "$INTERVAL"
done
