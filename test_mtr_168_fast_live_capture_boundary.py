
import unittest
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_168_fast_live_capture_boundary as m
)


class Tests(unittest.TestCase):

    def test_actual_runtime_callback(self):
        result = m.validate_runtime_boundary()
        self.assertEqual(
            result["callback"],
            "fast_live_attack",
        )

    def test_original_function_preserved(self):
        before = m.rt.canonical_price
        safe = m.make_capture_price(Mock())

        self.assertIs(m.rt.canonical_price, before)
        self.assertIsNot(safe, before)

    def test_correct_callback_replaced(self):
        callback = Mock()
        safe = m.make_capture_price(callback)

        self.assertIs(
            safe.__globals__["fast_live_attack"],
            callback,
        )

    def test_old_callback_not_used(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["attack"]()

    def test_compiler_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["compile_current"]()

    def test_simulator_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["simulate_current"]()

    def test_execution_function_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["_execute_route_once"]()

    def test_signer_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["signed_tx"]()

    def test_broadcast_blocked(self):
        safe = m.make_capture_price(Mock())

        with self.assertRaises(m.BoundaryHold):
            safe.__globals__["send"]()

    def test_public_wallet_only(self):
        wallet = "11111111111111111111111111111111"

        prepared = m.prepare_capture(
            wallet,
            "runtime_state/oracle/oracle_live_execution",
        )

        self.assertEqual(
            prepared["counters"]["captured"],
            0,
        )

        self.assertTrue(callable(prepared["price"]))

    def test_invalid_wallet_rejected(self):
        with self.assertRaises(m.BoundaryHold):
            m.prepare_capture("invalid", "unused")

    def test_no_production_mutation(self):
        before = m.rt.canonical_price
        before_globals = before.__globals__

        m.make_capture_price(Mock())

        self.assertIs(m.rt.canonical_price, before)
        self.assertIs(before.__globals__, before_globals)

        self.assertIsNot(
            before.__globals__["fast_live_attack"],
            m.forbidden,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
