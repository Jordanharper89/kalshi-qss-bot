
import unittest
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_167_live_capture_integration as m
)

class Tests(unittest.TestCase):

    def test_boundary_revision(self):
        self.assertEqual(
            m.REVISION,
            "MTR167_ISOLATED_LIVE_CAPTURE"
        )

    def test_execution_refused(self):
        with self.assertRaises(RuntimeError):
            m.forbidden()

    def test_no_wallet_no_launch(self):
        m.main([])

    def test_safe_price_is_independent(self):
        before = m.rt.canonical_price

        callback = Mock()

        safe = m.make_safe_price(callback)

        self.assertIs(m.rt.canonical_price, before)
        self.assertIsNot(safe, before)

        self.assertIs(
            safe.__globals__["attack"], callback
        )

    def test_compiler_blocked(self):
        safe = m.make_safe_price(Mock())

        with self.assertRaises(RuntimeError):
            safe.__globals__["compile_current"]()

    def test_simulation_blocked(self):
        safe = m.make_safe_price(Mock())

        with self.assertRaises(RuntimeError):
            safe.__globals__["simulate_current"]()

    def test_run_is_independent(self):
        price = m.make_safe_price(Mock())

        before = m.rt.run

        safe = m.make_safe_run(
            price,
            "11111111111111111111111111111111"
        )

        self.assertIs(m.rt.run, before)
        self.assertIsNot(safe, before)

        self.assertIs(
            safe.__globals__["canonical_price"],
            price
        )

    def test_public_identity_only(self):
        identity = m.public_identity(
            "11111111111111111111111111111111"
        )

        self.assertIsNone(identity[0])
        self.assertEqual(len(identity), 2)

    def test_no_mutating_production_globals(self):
        price_before = m.rt.canonical_price
        run_before = m.rt.run

        price = m.make_safe_price(Mock())
        m.make_safe_run(
            price,
            "11111111111111111111111111111111"
        )

        self.assertIs(m.rt.canonical_price, price_before)
        self.assertIs(m.rt.run, run_before)

if __name__ == "__main__":
    unittest.main(verbosity=2)
