"""hello-api: a small HTTP service used to exercise the platform.

Standard library only, so the container image has no third-party
dependencies to patch. Exposes:
  GET /            -> JSON greeting
  GET /healthz     -> liveness probe
  GET /readyz      -> readiness probe (fails while SHUTTING_DOWN is set)
  GET /metrics     -> Prometheus text format (request counts and latency)
"""

import json
import os
import signal
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

VERSION = os.environ.get("APP_VERSION", "dev")
GREETING = os.environ.get("GREETING", "hello from hello-api")

# Latency buckets in seconds, matching the SLO alert rules.
BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5)


class Metrics:
    """Thread-safe counters rendered in Prometheus exposition format."""

    def __init__(self):
        self._lock = threading.Lock()
        self.requests = {}  # (path, code) -> count
        self.bucket_counts = [0] * len(BUCKETS)
        self.latency_sum = 0.0
        self.latency_count = 0

    def observe(self, path, code, seconds):
        with self._lock:
            key = (path, str(code))
            self.requests[key] = self.requests.get(key, 0) + 1
            self.latency_sum += seconds
            self.latency_count += 1
            for i, le in enumerate(BUCKETS):
                if seconds <= le:
                    self.bucket_counts[i] += 1

    def render(self):
        with self._lock:
            lines = [
                "# HELP http_requests_total Total HTTP requests.",
                "# TYPE http_requests_total counter",
            ]
            for (path, code), n in sorted(self.requests.items()):
                lines.append(f'http_requests_total{{path="{path}",code="{code}"}} {n}')
            lines += [
                "# HELP http_request_duration_seconds Request latency.",
                "# TYPE http_request_duration_seconds histogram",
            ]
            for le, n in zip(BUCKETS, self.bucket_counts):
                lines.append(f'http_request_duration_seconds_bucket{{le="{le}"}} {n}')
            lines.append(f'http_request_duration_seconds_bucket{{le="+Inf"}} {self.latency_count}')
            lines.append(f"http_request_duration_seconds_sum {self.latency_sum:.6f}")
            lines.append(f"http_request_duration_seconds_count {self.latency_count}")
            lines.append(f'app_info{{version="{VERSION}"}} 1')
            return "\n".join(lines) + "\n"


METRICS = Metrics()
STATE = {"shutting_down": False}


class Handler(BaseHTTPRequestHandler):
    server_version = "hello-api"
    sys_version = ""  # don't advertise the Python version

    def _send(self, code, body, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802 (stdlib naming)
        start = time.monotonic()
        path = self.path.split("?", 1)[0]
        if path == "/":
            code, body = 200, json.dumps({"message": GREETING, "version": VERSION})
            self._send(code, body)
        elif path == "/healthz":
            code = 200
            self._send(code, json.dumps({"status": "ok"}))
        elif path == "/readyz":
            code = 503 if STATE["shutting_down"] else 200
            self._send(code, json.dumps({"ready": code == 200}))
        elif path == "/metrics":
            code = 200
            self._send(code, METRICS.render(), "text/plain; version=0.0.4")
        else:
            code = 404
            self._send(code, json.dumps({"error": "not found"}))
        # Keep label cardinality bounded: unknown paths are grouped.
        label = path if path in ("/", "/healthz", "/readyz", "/metrics") else "other"
        METRICS.observe(label, code, time.monotonic() - start)

    def log_message(self, fmt, *args):
        # One JSON line per request for log aggregation.
        print(json.dumps({"remote": self.client_address[0], "request": fmt % args}), flush=True)


def build_server(port):
    return ThreadingHTTPServer(("0.0.0.0", port), Handler)


def main():
    port = int(os.environ.get("PORT", "8080"))
    server = build_server(port)

    def graceful(signum, frame):
        # Fail readiness first so the Service stops routing to this pod,
        # then stop accepting connections.
        STATE["shutting_down"] = True
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, graceful)
    print(json.dumps({"event": "start", "port": port, "version": VERSION}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
