import inspect
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
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

    def test_reuses_oracle025_programs(self):
        src=inspect.getsource(
            q.prebuild_meteora_templates
        )

        self.assertIn(
            "warmed_rows",
            src
        )

        self.assertNotIn(
            "q87.c.account(",
            src
        )

    def test_reuses_pair_arrays(self):
        src=inspect.getsource(
            q.prebuild_meteora_templates
        )

        self.assertIn(
            "pair.arrays",
            src
        )

        self.assertNotIn(
            "dlmm_arrays(",
            src
        )

    def test_one_bitmap_batch(self):
        src=inspect.getsource(
            q.prebuild_meteora_templates
        )

        self.assertIn(
            '"getMultipleAccounts"',
            src
        )

    def test_hot_builder_zero_rpc(self):
        src=inspect.getsource(
            q.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
            "http(",
        ):
            self.assertNotIn(
                bad,
                src
            )

    def test_buy_exact_quote_preserved(self):
        src=inspect.getsource(
            q.rewrite_pump_buy_bounds
        )

        self.assertIn(
            "BUY_EXACT_QUOTE_IN_DISC",
            src
        )

    def test_truth_sim_preserved(self):
        src=inspect.getsource(
            q.simulate_current
        )

        self.assertIn(
            '"simulateTransaction"',
            src
        )

        self.assertIn(
            'result.get(\n        "value"',
            src
        )

    def test_no_old_execution_chain(self):
        src=inspect.getsource(q)

        self.assertNotIn(
            "q20.run(",
            src
        )

        self.assertNotIn(
            "persistent.serve(",
            src
        )

        self.assertNotIn(
            "SimulationLane(",
            src
        )

    def test_no_broadcast(self):
        src=inspect.getsource(q)

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
