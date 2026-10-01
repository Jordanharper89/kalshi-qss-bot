import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_086_two_second_dynamic_execution_binding_cutover as q


class T(unittest.TestCase):

    def test_exact_memory_source(self):
        self.assertTrue(
            hasattr(q.q80,"MEMORY")
        )


    def test_exact_hydration_path(self):
        self.assertTrue(
            callable(q.q47.prepare_from)
        )


    def test_exact_hydration_lock(self):
        self.assertTrue(
            callable(q.q80.acquire_hydration_lock)
        )

        self.assertTrue(
            callable(q.q80.release_hydration_lock)
        )


    def test_rpc_valve_exists(self):
        self.assertTrue(
            callable(q.rv.gated_rpc)
        )


    def test_2s_policy_reused(self):
        self.assertEqual(
            q.q85.TARGET_HORIZON,
            "2"
        )

        self.assertEqual(
            q.q85.MIN_2S_WIN_RATE,
            0.80
        )


    def test_atomic_composer_reused(self):
        self.assertTrue(
            callable(q.las.compose_bound)
        )


    def test_candidate_simulator_reused(self):
        self.assertTrue(
            callable(
                q.las.q59.attempt_candidate_simulations
            )
        )


    def test_compile_failure_diagnostic(self):
        x=q.classify_attempt({
            "compiled":False,
            "error":"ATOMIC_TX_TOO_LARGE:1300"
        })

        self.assertTrue(
            x.startswith("COMPILE_FAIL:")
        )


    def test_sim_pnl_diagnostic(self):
        x=q.classify_attempt({
            "compiled":True,
            "sim_err":None,
            "sim_pnl_lamports":-100,
            "sim_bps":-1,
        })

        self.assertEqual(
            x,
            "SIM_PNL_NONPOSITIVE"
        )


    def test_profitable_diagnostic(self):
        x=q.classify_attempt({
            "compiled":True,
            "profitable":True,
            "sim_err":None,
            "sim_pnl_lamports":100,
            "sim_bps":100,
        })

        self.assertEqual(
            x,
            "PROFITABLE_SIMULATION"
        )


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


if __name__=="__main__":
    unittest.main(verbosity=2)
