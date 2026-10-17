
import unittest
from unittest.mock import Mock

from qseries_v2.oracle_execution.solana_atomic_executor import (
    mtr_170_integrated_capture_runner as m
)


WALLET = "11111111111111111111111111111111"


class Tests(unittest.TestCase):

    def test_runtime_boundary(self):
        self.assertTrue(m.inspect_boundary())

    def test_capture_lane(self):
        result = m.prepare(WALLET, "unused")

        self.assertIs(
            result["safe_price"].__globals__["fast_live_attack"],
            result["callback"],
        )

    def test_isolated_run(self):
        prepared = m.prepare(WALLET, "unused")

        before = m.rt.run

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        self.assertIs(m.rt.run, before)
        self.assertIsNot(cloned, before)

    def test_public_identity(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        identity = (
            cloned.__globals__["q87"].c.sim_identity()
        )

        self.assertEqual(identity, (None, WALLET))

    def test_compilation_disabled(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        with self.assertRaises(m.CaptureHold):
            cloned.__globals__["compile_current"]()

    def test_signing_disabled(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        with self.assertRaises(m.CaptureHold):
            cloned.__globals__["signed_tx"]()

    def test_broadcast_disabled(self):
        prepared = m.prepare(WALLET, "unused")

        cloned = m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        with self.assertRaises(m.CaptureHold):
            cloned.__globals__["send"]()

    def test_duration_guard(self):
        with self.assertRaises(m.CaptureHold):
            m.run_capture(500, WALLET, "unused")

    def test_default_does_not_start_network(self):
        m.main([])

    def test_original_runtime_preserved(self):
        original_run = m.rt.run
        original_price = m.rt.canonical_price

        prepared = m.prepare(WALLET, "unused")

        m.make_isolated_run(
            WALLET,
            prepared["safe_price"],
        )

        self.assertIs(m.rt.run, original_run)
        self.assertIs(m.rt.canonical_price, original_price)


if __name__ == "__main__":
    unittest.main(verbosity=2)
