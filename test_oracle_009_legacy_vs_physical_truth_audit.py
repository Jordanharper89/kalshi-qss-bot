import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_009_legacy_vs_physical_truth_audit
    as q
)


class T(unittest.TestCase):

    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


    def test_original_sizes_present(self):
        for x in (
            0.05,
            0.1,
            0.18,
            0.28,
            0.5,
            0.9,
            1.4,
        ):
            self.assertIn(
                x,
                q.SIZE_SOL
            )


    def test_legacy_exact_path(self):
        s=inspect.getsource(
            q.compare_one
        )

        self.assertIn(
            "legacy.compose_bound",
            s
        )


    def test_physical_exact_path(self):
        s=inspect.getsource(
            q.compare_one
        )

        self.assertIn(
            "physical.physical_route_for_size",
            s
        )


    def test_stage_accounting_present(self):
        s=inspect.getsource(
            q.compare_one
        )

        for name in (
            "legacy_pump_token_out",
            "physical_pump_quote_out",
            "physical_pump_minimum_out",
            "physical_transfer_fee",
            "physical_pump_spendable_out",
            "physical_meteora_quote_out",
            "physical_meteora_min_out",
        ):
            self.assertIn(
                name,
                s
            )


    def test_no_packet_compile(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "compile_signed",
            s
        )

        self.assertNotIn(
            "getLatestBlockhash",
            s
        )


    def test_no_broadcast(self):
        s=open(
            q.__file__,
            encoding="utf-8"
        ).read()

        self.assertNotIn(
            "sendTransaction",
            s
        )

        self.assertNotIn(
            "send_once(",
            s
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
