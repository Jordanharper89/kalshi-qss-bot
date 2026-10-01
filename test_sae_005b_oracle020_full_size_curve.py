import inspect
import unittest

from qseries_v2.oracle_execution import (
    oracle_020_latest_state_exact_pricing_worker
    as q20
)

from qseries_v2.oracle_execution.solana_atomic_executor import (
    runtime as canonical
)


class T(unittest.TestCase):

    def test_safety(self):

        self.assertFalse(
            q20.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q20.PAPER_ONLY
        )

        self.assertFalse(
            q20.REAL_MONEY_MOVED
        )

        self.assertFalse(
            canonical.EXECUTION_AUTHORITY
        )

    def test_preferred_center(self):

        self.assertEqual(
            q20.PREFERRED_SIZE_SOL,
            0.180
        )

    def test_full_curve_exact(self):

        self.assertEqual(
            tuple(
                q20.FULL_SIZE_CURVE
            ),
            (
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
        )

    def test_every_size_is_primary(self):

        self.assertEqual(
            tuple(
                q20.FAST_SIZES
            ),
            tuple(
                q20.FULL_SIZE_CURVE
            )
        )

        self.assertEqual(
            tuple(
                q20.EXPAND_SIZES
            ),
            ()
        )

    def test_selection_is_max_net_lamports(self):

        src=inspect.getsource(
            q20.LatestStateLane._price
        )

        compact="".join(
            src.split()
        )

        self.assertIn(
            'max(rows,key=lambdax:x["local_net"])',
            compact
        )

    def test_every_primary_size_is_quoted(self):

        src=inspect.getsource(
            q20.LatestStateLane._price
        )

        self.assertIn(
            "for size in FAST_SIZES",
            src
        )

        self.assertIn(
            "q18.exact_snapshot_opportunities",
            src
        )

    def test_sae003_pricer_preserved(self):

        self.assertEqual(
            canonical.q18.WORKER_JS.name,
            "sae003_pump_exact_quote_worker.mjs"
        )

    def test_sae004_pump_contract_preserved(self):

        self.assertEqual(
            canonical.q87.PUMP_FIXED_ACCOUNTS,
            24
        )

    def test_hot_meteora_stays_rpc_free(self):

        src=inspect.getsource(
            canonical.build_meteora_ix_hot
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
            canonical.attack
        )

        self.assertIn(
            "pump_6040_actual_base_out",
            src
        )

        self.assertIn(
            "reprice_from_pump_chain_truth",
            src
        )

    def test_no_broadcast(self):

        src=inspect.getsource(
            canonical
        )

        self.assertNotIn(
            "sendTransaction",
            src
        )


if __name__=="__main__":

    unittest.main(
        verbosity=2
    )
