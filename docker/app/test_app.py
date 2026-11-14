"""Unit tests for the app. They run in the Dockerfile's test stage and in CI, with plain unittest."""

import http.client
import threading
import unittest
from http.server import ThreadingHTTPServer

from app import Handler, greeting


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.httpd.server_address[1]
        threading.Thread(target=cls.httpd.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read()
        conn.close()
        return resp.status, body

    def test_health(self):
        self.assertEqual(self.get("/health"), (200, b"ok\n"))

    def test_root_greets(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"Hello from inside a container", body)

    def test_unknown_path(self):
        self.assertEqual(self.get("/nope")[0], 404)

    def test_greeting_has_uid(self):
        self.assertIn("uid", greeting())


if __name__ == "__main__":
    unittest.main()
