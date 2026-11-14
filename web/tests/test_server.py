"""Tests for the caching server. They start it on a free localhost port."""

import http.client
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server import CachingHandler, etag_matches, make_etag  # noqa: E402
from http.server import ThreadingHTTPServer  # noqa: E402


@pytest.fixture(scope="module")
def port():
    # Port 0 asks the operating system for any free port.
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), CachingHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def request(port, method="GET", path="/", headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request(method, path, headers=headers or {})
    resp = conn.getresponse()
    body = resp.read()
    conn.close()
    return resp, body


def test_first_request_is_200_with_caching_headers(port):
    resp, body = request(port)
    assert resp.status == 200
    assert resp.getheader("Cache-Control") == "public, max-age=60"
    assert resp.getheader("ETag", "").startswith('"')
    assert resp.getheader("Content-Type") == "text/html; charset=utf-8"
    assert int(resp.getheader("Content-Length")) == len(body)
    assert b"Hello from a tiny server" in body


def test_same_etag_gives_304_with_no_body(port):
    first, _ = request(port)
    etag = first.getheader("ETag")

    second, body = request(port, headers={"If-None-Match": etag})
    assert second.status == 304
    assert body == b""
    assert second.getheader("ETag") == etag
    assert second.getheader("Cache-Control") == "public, max-age=60"


def test_different_etag_gives_200(port):
    resp, body = request(port, headers={"If-None-Match": '"not-the-current-version"'})
    assert resp.status == 200
    assert body


def test_etag_is_stable_between_requests(port):
    a, _ = request(port)
    b, _ = request(port)
    assert a.getheader("ETag") == b.getheader("ETag")


def test_head_sends_headers_but_no_body(port):
    resp, body = request(port, method="HEAD")
    assert resp.status == 200
    assert resp.getheader("ETag")
    assert body == b""


def test_unknown_path_is_404(port):
    resp, _ = request(port, path="/nope")
    assert resp.status == 404


@pytest.mark.parametrize(
    "header, expected",
    [
        ('"abc"', True),
        ('W/"abc"', True),
        ('"x", "abc"', True),
        ("*", True),
        ('"x"', False),
        ("", False),
    ],
)
def test_etag_matching_rules(header, expected):
    assert etag_matches(header, '"abc"') is expected


def test_etag_changes_when_content_changes():
    assert make_etag(b"one") != make_etag(b"two")
