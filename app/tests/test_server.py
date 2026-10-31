"""Unit and integration tests for hello-api (stdlib unittest, no dependencies)."""

import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import server  # noqa: E402


class MetricsTest(unittest.TestCase):
    def test_counts_and_buckets(self):
        m = server.Metrics()
        m.observe("/", 200, 0.03)
        m.observe("/", 200, 0.3)
        out = m.render()
        self.assertIn('http_requests_total{path="/",code="200"} 2', out)
        self.assertIn('http_request_duration_seconds_bucket{le="0.05"} 1', out)
        self.assertIn('http_request_duration_seconds_bucket{le="0.5"} 2', out)
        self.assertIn('http_request_duration_seconds_bucket{le="+Inf"} 2', out)


class ServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.build_server(0)  # port 0 = pick a free port
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path, timeout=5) as r:
                return r.status, r.headers, r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read().decode()

    def test_root(self):
        code, headers, body = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn("message", json.loads(body))
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")

    def test_health(self):
        self.assertEqual(self.get("/healthz")[0], 200)

    def test_readiness_flips_on_shutdown(self):
        self.assertEqual(self.get("/readyz")[0], 200)
        server.STATE["shutting_down"] = True
        try:
            self.assertEqual(self.get("/readyz")[0], 503)
        finally:
            server.STATE["shutting_down"] = False

    def test_unknown_path_is_404_and_grouped(self):
        self.assertEqual(self.get("/nope?x=1")[0], 404)
        _, _, metrics = self.get("/metrics")
        self.assertIn('path="other",code="404"', metrics)

    def test_no_version_leak_in_server_header(self):
        _, headers, _ = self.get("/")
        self.assertNotIn("Python", headers.get("Server", ""))


if __name__ == "__main__":
    unittest.main()
