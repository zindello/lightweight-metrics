"""lightweight-metrics: a small Prometheus text endpoint (/metrics) and a liveness check
(/healthz), in pure Python, with no dependencies: the figures are a handful of gauges and counters,
set each tick. See README.md."""

import http.server
import threading

__version__ = "0.1.0"

__all__ = ["Registry", "serve", "__version__"]


def _escape(v):
    return str(v).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


class Registry:
    def __init__(self):
        self.lock = threading.Lock()
        self.meta = {}       # name -> (type, help)
        self.values = {}     # (name, labels tuple) -> value
        self.health = lambda: (True, "ok")

    def describe(self, name, kind, help_text):
        self.meta[name] = (kind, help_text)

    def set(self, name, value, /, **labels):
        if value is None:
            return
        with self.lock:
            self.values[(name, tuple(sorted(labels.items())))] = float(value)

    def inc(self, name, by=1.0, /, **labels):
        key = (name, tuple(sorted(labels.items())))
        with self.lock:
            self.values[key] = self.values.get(key, 0.0) + by

    def get(self, name, /, **labels):
        return self.values.get((name, tuple(sorted(labels.items()))))

    def clear(self, name):
        with self.lock:
            for key in [k for k in self.values if k[0] == name]:
                del self.values[key]

    def render(self):
        with self.lock:
            items = sorted(self.values.items())
        lines, seen = [], set()
        for (name, labels), value in items:
            if name not in seen:
                seen.add(name)
                kind, help_text = self.meta.get(name, ("gauge", ""))
                if help_text:
                    lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} {kind}")
            label_text = ",".join(f'{k}="{_escape(v)}"' for k, v in labels)
            # repr: every digit a float has. ":g" kept six, so a Unix time read 1.7937e+09, off by
            # up to 5,000 s, and FanControlHeartbeatStale fired half the time (3 November).
            text = repr(value)
            lines.append(f"{name}{{{label_text}}} {text}" if label_text else f"{name} {text}")
        return "\n".join(lines) + "\n"


def serve(registry, port):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/metrics":
                body, code = registry.render().encode(), 200
                ctype = "text/plain; version=0.0.4"
            elif self.path == "/healthz":
                ok, text = registry.health()
                body, code, ctype = text.encode(), 200 if ok else 503, "text/plain"
            else:
                body, code, ctype = b"not found\n", 404, "text/plain"
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, name="metrics", daemon=True).start()
    return server
