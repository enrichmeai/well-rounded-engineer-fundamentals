"""A tiny web app to put in a container. Standard library only.

GET /        -> a greeting, plus the user id the process runs as (so you can see it is not root)
GET /health  -> "ok", for the container's HEALTHCHECK
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def greeting() -> dict:
    return {"message": "Hello from inside a container", "uid": os.getuid()}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, "text/plain; charset=utf-8", b"ok\n")
        elif self.path == "/":
            body = (json.dumps(greeting()) + "\n").encode()
            self._send(200, "application/json", body)
        else:
            self._send(404, "text/plain; charset=utf-8", b"not found\n")

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    # Inside a container, listen on all interfaces (0.0.0.0), or the published port cannot reach us.
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8080"))
    with ThreadingHTTPServer((host, port), Handler) as httpd:
        print(f"Listening on {host}:{port}", flush=True)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
