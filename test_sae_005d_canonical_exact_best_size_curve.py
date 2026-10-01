import inspect
import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as q
)


EXPECTED=(
    0.001,
    0.010,
    0.025,
    0.050,
    0.100,
    0.180,
    0.280,
    0.500,
    1.000,
    1.400,
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

    def test_exact_best_is_canonical_target(self):
        src=inspect.getsource(
            q.exact_best
        )

        self.assertIn(
            "SAE-005D canonical dynamic economic size curve",
            src
        )

    def test_all_sizes_present(self):
        src=inspect.getsource(
            q.exact_best
        )

        for size in EXPECTED:
            self.assertIn(
                f"{size:.3f}",
                src
            )

    def test_prices_every_size(self):
        src=inspect.getsource(
            q.exact_best
        )

        self.assertIn(
            "for size in sizes",
            src
        )

        self.assertIn(
            "q18.exact_snapshot_opportunities",
            src
        )

    def test_selects_max_net_lamports(self):
        src="".join(
            inspect.getsource(
                q.exact_best
            ).split()
        )

        self.assertIn(
            'returnmax(rows,key=lambdax:int(x["local_net"]))',
            src
        )

    def test_canonical_price_calls_exact_best(self):
        src=inspect.getsource(
            q.canonical_price
        )

        self.assertIn(
            "exact_best(",
            src
        )

    def test_sae001_meteora_hot_preserved(self):
        src=inspect.getsource(
            q.build_meteora_ix_hot
        )

        for bad in (
            "c.rpc(",
            "c.account(",
            "dlmm_arrays(",
            "urlopen(",
        ):
            self.assertNotIn(
                bad,
                src
            )

    def test_sae002_truth_gate_preserved(self):
        src=inspect.getsource(
            q.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_sae003_exact_quote_preserved(self):
        self.assertEqual(
            q.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_sae004_pool_v2_preserved(self):
        self.assertEqual(
            q.q87.PUMP_FIXED_ACCOUNTS,
            24
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
