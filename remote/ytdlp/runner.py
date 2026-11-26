"""yt-dlp runner: does Aurral's YouTube lookups for the media host.

POST /run with "Authorization: Bearer <RUNNER_TOKEN>" and {"args": [...]}
answers {"code": <exit code>, "stdout": "...", "stderr": "..."}.
GET /health answers "ok" without starting yt-dlp.

Only the read-only options Aurral searches with are accepted, and only for a
YouTube URL or a ytsearch query. --dump-json never downloads or writes files,
so the token can't be used for anything but looking things up on YouTube.
If the caller hangs up (Aurral gave up on the search), yt-dlp is stopped.
"""
import hmac
import json
import os
import re
import select
import signal
import socket
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = os.environ["RUNNER_TOKEN"]
PORT = int(os.environ.get("PORT", "8291"))
SLOTS = threading.BoundedSemaphore(int(os.environ.get("MAX_PARALLEL", "4")))
TIME_LIMIT = int(os.environ.get("TIME_LIMIT_SECONDS", "120"))

FLAGS = {"--flat-playlist", "--dump-json", "--no-warnings", "--skip-download", "--no-download",
         "--no-js-runtimes", "--"}
WITH_VALUE = {"--playlist-end": re.compile(r"[0-9]{1,3}"), "--js-runtimes": re.compile(r"node")}
TARGET = re.compile(r"https://(?:music|www)\.youtube\.com/\S{1,2000}|ytsearch[0-9]{0,2}:[^\x00]{1,500}", re.S)


def allowed(args):
    """A lookup Aurral makes: known flags only, --dump-json, exactly one YouTube target."""
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        return False
    targets, i = 0, 0
    while i < len(args):
        if args[i] in FLAGS:
            i += 1
        elif args[i] in WITH_VALUE and i + 1 < len(args) and WITH_VALUE[args[i]].fullmatch(args[i + 1]):
            i += 2
        elif TARGET.fullmatch(args[i]):
            targets, i = targets + 1, i + 1
        else:
            return False
    return targets == 1 and "--dump-json" in args


def caller_gone(sock):
    try:
        readable, _, _ = select.select([sock], [], [], 0)
        return bool(readable) and sock.recv(1, socket.MSG_PEEK) == b""
    except OSError:
        return True


def run(args, sock):
    """Run yt-dlp; (None, ...) if the caller hung up, exit code 124 at the time limit."""
    proc = subprocess.Popen(["yt-dlp", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    result = {}
    reader = threading.Thread(target=lambda: result.update(zip(("out", "err"), proc.communicate())))
    reader.start()
    deadline = time.monotonic() + TIME_LIMIT
    while reader.is_alive():
        reader.join(0.5)
        if not reader.is_alive():
            break
        gone = caller_gone(sock)
        if gone or time.monotonic() > deadline:
            os.killpg(proc.pid, signal.SIGKILL)
            reader.join()
            if gone:
                return None, "", ""
            return 124, "", f"yt-dlp runner: stopped after {TIME_LIMIT} s"
    decode = lambda data: (data or b"").decode("utf-8", "replace")
    return proc.returncode, decode(result.get("out")), decode(result.get("err"))


class Handler(BaseHTTPRequestHandler):
    server_version = "ytdlp-runner"

    def log_message(self, *_):  # one line per run instead, without the search text
        pass

    def reply(self, status, body, content_type="application/json"):
        data = body.encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, "ok\n", "text/plain")
        self.reply(404, '{"error": "not found"}')

    def do_POST(self):
        if self.path != "/run":
            return self.reply(404, '{"error": "not found"}')
        if not hmac.compare_digest(self.headers.get("Authorization", "").encode(), f"Bearer {TOKEN}".encode()):
            return self.reply(401, '{"error": "unauthorized"}')
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 65536:
                raise ValueError
            args = json.loads(self.rfile.read(length))["args"]
        except (ValueError, KeyError, TypeError):
            return self.reply(400, '{"error": "bad request"}')
        if not allowed(args):
            print(f"refused {self.client_address[0]}: {[a for a in args if a.startswith('-')]}", flush=True)
            return self.reply(403, '{"error": "arguments not allowed"}')
        with SLOTS:
            started = time.monotonic()
            code, out, err = run(args, self.connection)
        kind = "search" if any(a.startswith("ytsearch") or "/search?" in a for a in args) else "read"
        status = "caller left" if code is None else f"exit {code}"
        print(f"{kind} {status} in {time.monotonic() - started:.1f} s", flush=True)
        if code is not None:
            self.reply(200, json.dumps({"code": code, "stdout": out, "stderr": err}))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.daemon_threads = True
    print(f"yt-dlp runner listening on :{PORT}", flush=True)
    server.serve_forever()
