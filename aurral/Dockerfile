# Aurral with more time for YouTube Music searches.
#
# Aurral gives a whole YouTube Music song search 15 s (SONG_SEARCH_BUDGET_MS,
# hard-coded in 3.1.0). On this host a single yt-dlp call takes 4-10 s, so the
# search ran out of time before it had read a single song, and tracks that only
# YouTube has (many Indian indie releases) failed with "No suitable search
# results". 60 s is plenty here.
#
# The build fails if that line changes upstream, so an Aurral update can't
# silently drop the patch: check whether it's still needed, then adjust or
# delete this file and go back to the plain image.
ARG AURRAL_VERSION=3.1.0
FROM ghcr.io/lklynet/aurral:${AURRAL_VERSION}

RUN f=/app/backend/services/ytdlpClient.ts \
 && grep -qx 'const SONG_SEARCH_BUDGET_MS = 15000;' "$f" \
 && sed -i 's/^const SONG_SEARCH_BUDGET_MS = 15000;$/const SONG_SEARCH_BUDGET_MS = 60000;/' "$f" \
 && grep -qx 'const SONG_SEARCH_BUDGET_MS = 60000;' "$f"
