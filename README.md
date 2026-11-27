# lightweight-metrics

A Prometheus text endpoint (`/metrics`) and a liveness check (`/healthz`), in pure Python, with no
dependencies. For small programs whose figures are a handful of gauges and counters, set each
tick, that don't want `prometheus_client` and its dependencies in their image.

```python
from lightweight_metrics import Registry, serve

metrics = Registry()
metrics.describe("perc_array_state", "gauge", "Each array's state: 0 optimal, 1 degraded, 2 failed.")
metrics.set("perc_array_state", 0, array="0")       # a value of None is left out
metrics.inc("perc_read_errors_total", reason="timeout")
metrics.health = lambda: (True, "ok")               # /healthz: 200, or 503 with your text
serve(metrics, 9101)                                # a daemon thread; returns the server
```

- Every value is a float, written with every digit it has (`repr`): a Unix time keeps its
  fractions, where `:g` would round it to six digits.
- Labels are sorted and escaped as Prometheus's text format wants. `clear(name)` drops a name's
  every series, for figures whose label sets change from one tick to the next.
- One lock guards the values; `serve` answers each request on its own thread.

## How it came about

Three programs on a small Kubernetes cluster of Dell servers, a T620's fan controller, its GPU
power caps and a PERC RAID monitor, each carried a byte-identical copy of this file. A code review
found the copies and asked for one, shared. This is that file, with its tests.

## Install

Pin a release tag, which can't be moved or deleted:

```text
lightweight-metrics @ git+https://github.com/zindello/lightweight-metrics@v0.1.0
```

A git requirement can't carry a hash, so install it without `--require-hashes`; the tag is the
pin. The build needs nothing from PyPI (`_build/backend.py`).

## Tests

```sh
python -m unittest discover -s tests -v
```

## Releasing

Bump the version in `pyproject.toml` and `__version__` (a test checks they match), merge the pull
request, then tag the merge commit `vX.Y.Z` and push the tag. Each program that uses it moves to
the new tag by its own pull request (Renovate opens them).

MIT licence.
