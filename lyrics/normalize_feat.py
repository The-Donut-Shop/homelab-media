"""Make lyric lookups use each track's primary artist.

beets-getlrc queries LRCLIB with `albumartist or artist` and no album name, so:
  - an album credited differently from its tracks (e.g. album artist "Ye", tracks
    "Kanye West") is looked up under the wrong name, and
  - "Artist feat. Guest" rarely matches LRCLIB, which lists the primary artist.
This sets both fields IN THE BEETS INDEX ONLY to the track's primary artist
("Artist feat. Guest" -> "Artist"). Audio files are never written; beets is used
here purely as an index for the lyrics fetcher. Changed tracks have their cached
lookup result cleared so beets-getlrc retries them.
"""
import re

from beets import config
from beets.library import Library

config.read(user=True, defaults=True)
lib = Library(config["library"].as_filename(), config["directory"].as_filename())
featured = re.compile(r"\s+(?:feat\.?|ft\.?|featuring)\s+.*$", re.IGNORECASE)

changed = 0
for item in lib.items():
    primary = featured.sub("", item.artist or "").strip()
    if not primary:
        continue
    if item.artist != primary or item.albumartist != primary:
        item.artist = primary
        item.albumartist = primary
        for key in ("getlrc_status", "getlrc_checked"):
            if key in item:
                del item[key]
        item.store()  # database only
        changed += 1
if changed:
    print(f"lookup artist normalised for {changed} track(s) in the index")
