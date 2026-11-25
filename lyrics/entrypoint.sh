#!/bin/sh
# Writes synced lyrics (.lrc) next to every track, shortly after it lands.
#
# Every CHECK_SECONDS (default 2 min) it looks for audio files newer than the
# last run - a cheap metadata-only check. Only when new music has arrived does
# it import those album folders into the beets index (as-is: no tagging,
# copying, moving or writing; new tracks are merged into albums beets already
# knows) and run beets-getlrc. getlrc skips tracks that already have a .lrc
# and caches "not found", so LRCLIB isn't hammered.
# Once a day (FULL_SECONDS) it does a full pass to pick up lyrics LRCLIB added
# later and to drop deleted tracks from the index. The time of the last full
# pass is kept on disk, so a restart (or a whole-host reboot, when every app is
# starting at once) doesn't trigger an extra one.
set -u
CHECK="${CHECK_SECONDS:-120}"
FULL="${FULL_SECONDS:-86400}"
STAMP=/config/.last-run
FULLSTAMP=/config/.last-full
AUDIO='.*\.\(flac\|mp3\|m4a\|opus\|ogg\|oga\|wav\|aac\|alac\|aiff\|wv\|ape\)'

log() { echo "[$(date -Iseconds)] $*"; }

full_pass() {
  log "full pass: indexing /music"
  touch "$STAMP.next"
  beet import -q -A -C -W -I /music >/dev/null 2>&1 || log "  import reported an error (see /config/import.log)"
  beet update >/dev/null 2>&1 || true
  python3 /usr/local/bin/normalize_feat.py || true
  beet getlrc -q || log "  getlrc returned an error"
  mv "$STAMP.next" "$STAMP"
  touch "$FULLSTAMP"
}

full_due() {
  [ -f "$STAMP" ] && [ -f "$FULLSTAMP" ] || return 0
  [ $(( $(date +%s) - $(stat -c %Y "$FULLSTAMP") )) -ge "$FULL" ]
}

while true; do
  if full_due; then
    full_pass
  else
    dirs=$(find /music -type f -iregex "$AUDIO" -newer "$STAMP" -printf '%h\n' 2>/dev/null | sort -u)
    if [ -n "$dirs" ]; then
      touch "$STAMP.next"
      echo "$dirs" | while IFS= read -r d; do
        log "new tracks in: ${d#/music/}"
        beet import -q -A -C -W -I "$d" >/dev/null 2>&1 || log "  import reported an error"
      done
      python3 /usr/local/bin/normalize_feat.py || true
      beet getlrc -q || log "  getlrc returned an error"
      mv "$STAMP.next" "$STAMP"
    fi
  fi
  sleep "$CHECK"
done
