
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_169_capture_lane_integration as m
)


class Tests(unittest.TestCase):

    def setUp(self):
        self.wallet = "11111111111111111111111111111111"
        self.output = "runtime_state/oracle/oracle_live_execution"

    def test_correct_boundary(self):
        self.assertEqual(
            m.m168.validate_runtime_boundary()["callback"],
            "fast_live_attack",
        )

    def test_lane_instance(self):
        result = m.verify_lane(self.wallet, self.output)

        self.assertIsInstance(
            result["lane"],
            m.rt.q20.LatestStateLane,
        )

    def test_price_method_binding(self):
        result = m.verify_lane(self.wallet, self.output)

        self.assertIs(
            result["lane"]._price.__func__,
            result["safe_price"],
        )

    def test_callback_identity(self):
        result = m.verify_lane(self.wallet, self.output)

        self.assertIs(
            result["safe_price"].__globals__["fast_live_attack"],
            result["callback"],
        )

    def test_compiler_guard(self):
        result = m.verify_lane(self.wallet, self.output)

        with self.assertRaises(m.m168.BoundaryHold):
            result["safe_price"].__globals__["compile_current"]()

    def test_simulation_guard(self):
        result = m.verify_lane(self.wallet, self.output)

        with self.assertRaises(m.m168.BoundaryHold):
            result["safe_price"].__globals__["simulate_current"]()

    def test_production_unchanged(self):
        before_price = m.rt.canonical_price
        before_attack = m.rt.fast_live_attack

        m.verify_lane(self.wallet, self.output)

        self.assertIs(m.rt.canonical_price, before_price)
        self.assertIs(m.rt.fast_live_attack, before_attack)

    def test_counters_fresh(self):
        first = m.verify_lane(self.wallet, self.output)
        second = m.verify_lane(self.wallet, self.output)

        self.assertIsNot(first["counters"], second["counters"])
        self.assertEqual(first["counters"]["captured"], 0)
        self.assertEqual(second["counters"]["captured"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
