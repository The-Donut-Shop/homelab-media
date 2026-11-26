#!/usr/bin/env python3
"""yt-dlp for Aurral, installed as /usr/local/bin/yt-dlp.

YouTube lookups (--dump-json, which never downloads) go to the yt-dlp runner on
the second machine (YTDLP_REMOTE_URL, see remote/ytdlp/), so they don't take RAM
and CPU on this host. Downloads, and every call while the runner is unreachable
or refuses, run here with the real yt-dlp (yt-dlp-local).
"""
import http.client
import json
import os
import sys
import urllib.parse

LOCAL = "/usr/local/bin/yt-dlp-local"
args = sys.argv[1:]
remote = os.environ.get("YTDLP_REMOTE_URL", "").strip()
token = os.environ.get("YTDLP_REMOTE_TOKEN", "").strip()


def run_here():
    os.execv(LOCAL, [LOCAL, *args])


if not remote or not token or "--dump-json" not in args or "--cookies" in args:
    run_here()

result = None
try:
    url = urllib.parse.urlsplit(remote)
    conn = http.client.HTTPConnection(url.hostname, url.port or 80, timeout=3)
    conn.connect()  # gives up within 3 s when the runner is down
    conn.sock.settimeout(180)
    conn.request("POST", "/run", json.dumps({"args": args}),
                 {"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    response = conn.getresponse()
    if response.status == 200:
        result = json.loads(response.read())
except (OSError, ValueError, http.client.HTTPException):
    pass
if result is None:
    run_here()

sys.stdout.buffer.write(result["stdout"].encode("utf-8"))
sys.stderr.buffer.write(result["stderr"].encode("utf-8"))
sys.exit(int(result["code"]))
