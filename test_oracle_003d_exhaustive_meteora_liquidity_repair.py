import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_003_unified_physical_execution_engine
    as q
)


class T(unittest.TestCase):

    def test_principal(self):
        self.assertEqual(
            q.MICRO_LAMPORTS,
            1_000_000
        )


    def test_strategy_is_pump_to_meteora(self):
        s=inspect.getsource(
            q.exact_route
        )

        self.assertIn(
            "native_pump_buy_ixs",
            s
        )

        self.assertIn(
            "meteora_swap",
            s
        )


    def test_meteora_diagnostics(self):
        s=inspect.getsource(
            q.meteora_swap
        )

        self.assertIn(
            "quote_source",
            s
        )

        self.assertIn(
            "loadedBinArrays",
            s
        )


    def test_paper_one_sweep(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "[PAPER_HOLD]",
            s
        )


    def test_signed_simulation_preserved(self):
        s=inspect.getsource(
            q.prepare_exact_packet
        )

        self.assertIn(
            "signed_simulation",
            s
        )


    def test_oracle_owner(self):
        self.assertEqual(
            q.EXECUTION_OWNER,
            "ORACLE"
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
