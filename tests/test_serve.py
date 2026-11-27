"""The endpoint: /metrics, /healthz and nothing else."""

import socket
import unittest
import urllib.error
import urllib.request

from lightweight_metrics import Registry, serve


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Serve(unittest.TestCase):
    def setUp(self):
        self.registry = Registry()
        self.port = free_port()
        self.server = serve(self.registry, self.port)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def get(self, path):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as r:
                return r.status, r.headers["Content-Type"], r.read().decode()
        except urllib.error.HTTPError as e:
            return e.code, e.headers["Content-Type"], e.read().decode()

    def test_metrics(self):
        self.registry.set("up", 1)
        self.assertEqual(self.get("/metrics"), (200, "text/plain; version=0.0.4", "# TYPE up gauge\nup 1.0\n"))

    def test_healthz_follows_the_check(self):
        self.assertEqual(self.get("/healthz"), (200, "text/plain", "ok"))
        self.registry.health = lambda: (False, "no read for 5 minutes")
        self.assertEqual(self.get("/healthz"), (503, "text/plain", "no read for 5 minutes"))

    def test_anything_else_is_404(self):
        self.assertEqual(self.get("/")[0], 404)


if __name__ == "__main__":
    unittest.main()
