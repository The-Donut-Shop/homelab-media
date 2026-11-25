# Synced-lyrics sidecar writer.
# beets (library index) + beets-getlrc (fetches .lrc files from lrclib.net).
# beets is configured to never move, copy, retag or rewrite audio files;
# the only thing this container ever writes into the music folder is "<track>.lrc".
FROM python:3.12-slim

RUN pip install --no-cache-dir "beets==2.14.1" "beets-getlrc==0.1.16"

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY normalize_feat.py /usr/local/bin/normalize_feat.py
RUN chmod 0755 /usr/local/bin/entrypoint.sh

ENV BEETSDIR=/config
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
