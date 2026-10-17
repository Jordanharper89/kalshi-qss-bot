
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_171_rotating_capture_safety as m
)

class Tests(unittest.TestCase):

    def test_real_rotating_entrypoint(self):
        self.assertTrue(callable(m.rt.serve_rotating))

    def test_actual_run_binding(self):
        self.assertIn(
            "serve_rotating",
            m.rt.run.__code__.co_names,
        )

    def test_actual_pricing_binding(self):
        self.assertIn(
            "fast_live_attack",
            m.rt.canonical_price.__code__.co_names,
        )

    def test_report_not_authorized(self):
        report = m.inspect_runtime()

        self.assertFalse(
            report["live_capture_authorized"]
        )
        self.assertFalse(
            report["signing_authorized"]
        )
        self.assertFalse(
            report["broadcast_authorized"]
        )

    def test_original_functions_unchanged(self):
        before = (
            m.rt.run,
            m.rt.serve_rotating,
            m.rt.canonical_price,
        )

        m.inspect_runtime()

        after = (
            m.rt.run,
            m.rt.serve_rotating,
            m.rt.canonical_price,
        )

        self.assertEqual(before, after)

if __name__ == "__main__":
    unittest.main(verbosity=2)
