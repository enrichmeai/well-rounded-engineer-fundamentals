"""A tiny HTTP server that makes caching visible.

It serves one page at "/" with three caching headers:

* Cache-Control: tells the browser (and any cache in between) how long it may
  reuse the page without asking again.
* ETag: a fingerprint of the page's bytes. If the page changes, so does the ETag.
* Conditional GET: when the client sends the ETag back in If-None-Match and it
  still matches, the server answers 304 Not Modified with no body.

Standard library only. Run it with:  python3 server.py  (then open http://127.0.0.1:8000/)
"""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PAGE = b"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Caching, made visible</title></head>
<body>
<h1>Hello from a tiny server</h1>
<p>Open your browser's developer tools, Network tab, and reload this page.
The first load is <code>200 OK</code>; a reload can be <code>304 Not Modified</code>.</p>
</body>
</html>
"""

# How long (in seconds) a cache may reuse the page before it must check again.
MAX_AGE = 60


def make_etag(body: bytes) -> str:
    """A strong ETag: a quoted hash of the exact bytes we send."""
    return '"' + hashlib.sha256(body).hexdigest()[:16] + '"'


def etag_matches(if_none_match: str, etag: str) -> bool:
    """True if the If-None-Match header names our ETag (or is the wildcard "*").

    The header may list several ETags separated by commas, and may use the
    weak form W/"...". For If-None-Match a weak comparison is used, so the W/
    prefix is ignored.
    """
    for candidate in if_none_match.split(","):
        candidate = candidate.strip()
        if candidate == "*":
            return True
        if candidate.startswith("W/"):
            candidate = candidate[2:]
        if candidate == etag:
            return True
    return False


class CachingHandler(BaseHTTPRequestHandler):
    server_version = "TinyCachingServer/1.0"

    def _send_page(self, include_body: bool) -> None:
        if self.path not in ("/", "/index.html"):
            self.send_error(404, "Not Found")
            return

        etag = make_etag(PAGE)
        if_none_match = self.headers.get("If-None-Match")

        if if_none_match is not None and etag_matches(if_none_match, etag):
            # The client already has this exact version: say so, send no body.
            self.send_response(304)
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", f"public, max-age={MAX_AGE}")
            self.end_headers()
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(PAGE)))
        self.send_header("ETag", etag)
        self.send_header("Cache-Control", f"public, max-age={MAX_AGE}")
        self.end_headers()
        if include_body:
            self.wfile.write(PAGE)

    def do_GET(self) -> None:  # noqa: N802 (name required by BaseHTTPRequestHandler)
        self._send_page(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._send_page(include_body=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve one page with caching headers.")
    parser.add_argument("--host", default="127.0.0.1", help="address to listen on (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="port to listen on (default 8000)")
    args = parser.parse_args()

    with ThreadingHTTPServer((args.host, args.port), CachingHandler) as httpd:
        print(f"Serving on http://{args.host}:{args.port}/  (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
