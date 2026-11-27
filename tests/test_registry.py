"""The /metrics text, as Prometheus reads it."""

import unittest

from lightweight_metrics import Registry


class Render(unittest.TestCase):
    def test_values_keep_every_digit(self):
        # ":g" kept six digits, so a Unix time read 1.7937e+09 and a heartbeat alert fired half
        # the time (the fan controller, 3 November 2026).
        r = Registry()
        r.set("heartbeat_timestamp_seconds", 1793702393.6407595)
        r.set("writes_total", 12345678.0, zone="cpu")
        lines = r.render().splitlines()
        self.assertIn("heartbeat_timestamp_seconds 1793702393.6407595", lines)
        self.assertIn('writes_total{zone="cpu"} 12345678.0', lines)

    def test_help_and_type_once_per_name(self):
        r = Registry()
        r.describe("duty_percent", "gauge", "Each zone's duty.")
        r.set("duty_percent", 40, zone="cpu")
        r.set("duty_percent", 30, zone="pci")
        self.assertEqual(r.render().splitlines(), [
            "# HELP duty_percent Each zone's duty.",
            "# TYPE duty_percent gauge",
            'duty_percent{zone="cpu"} 40.0',
            'duty_percent{zone="pci"} 30.0',
        ])

    def test_undescribed_is_a_gauge_with_no_help(self):
        r = Registry()
        r.set("up", 1)
        self.assertEqual(r.render(), "# TYPE up gauge\nup 1.0\n")

    def test_labels_sorted_and_escaped(self):
        r = Registry()
        r.set("x", 1, b='say "hi"\\\n', a="1")
        self.assertIn('x{a="1",b="say \\"hi\\"\\\\\\n"} 1.0', r.render().splitlines())

    def test_none_leaves_the_value_out(self):
        r = Registry()
        r.set("temp", None, card="0")
        self.assertIsNone(r.get("temp", card="0"))
        self.assertEqual(r.render(), "\n")

    def test_inc_get_and_clear(self):
        r = Registry()
        r.inc("errors_total", kind="a")
        r.inc("errors_total", 2, kind="a")
        r.set("other", 5)
        self.assertEqual(r.get("errors_total", kind="a"), 3.0)
        r.clear("errors_total")
        self.assertIsNone(r.get("errors_total", kind="a"))
        self.assertEqual(r.get("other"), 5.0)


if __name__ == "__main__":
    unittest.main()
