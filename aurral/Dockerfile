# Aurral, adjusted for a slow 8 GB host. Each step fails the build if upstream
# changes the code it relies on, so an Aurral update can't silently drop it:
# check whether it's still needed, then adjust it or go back to the plain image.
ARG AURRAL_VERSION=3.1.0
FROM ghcr.io/lklynet/aurral:${AURRAL_VERSION}

# 1. More time for YouTube Music searches. Aurral gives a whole song search 15 s
#    (SONG_SEARCH_BUDGET_MS, hard-coded in 3.1.0). On this host a single yt-dlp
#    call takes 4-10 s, so the search ran out of time before it had read a
#    single song, and tracks that only YouTube has (many Indian indie releases)
#    failed with "No suitable search results".
RUN f=/app/backend/services/ytdlpClient.ts \
 && grep -qx 'const SONG_SEARCH_BUDGET_MS = 15000;' "$f" \
 && sed -i 's/^const SONG_SEARCH_BUDGET_MS = 15000;$/const SONG_SEARCH_BUDGET_MS = 60000;/' "$f" \
 && grep -qx 'const SONG_SEARCH_BUDGET_MS = 60000;' "$f"

# 2. YouTube lookups run on the second machine. Aurral runs `yt-dlp` from PATH;
#    this puts ytdlp-remote.py in its place, which sends lookups to the runner
#    in remote/ytdlp/ when YTDLP_REMOTE_URL is set and runs everything else (and
#    everything while the runner is down) with the real yt-dlp, kept as yt-dlp-local.
COPY ytdlp-remote.py /usr/local/bin/yt-dlp-remote
RUN grep -q 'function getBinaryPath() {' /app/backend/services/ytdlpClient.ts \
 && grep -q 'return DEFAULT_BINARY;' /app/backend/services/ytdlpClient.ts \
 && test -x /usr/local/bin/yt-dlp \
 && mv /usr/local/bin/yt-dlp /usr/local/bin/yt-dlp-local \
 && mv /usr/local/bin/yt-dlp-remote /usr/local/bin/yt-dlp \
 && chmod 0755 /usr/local/bin/yt-dlp \
 && yt-dlp --version
