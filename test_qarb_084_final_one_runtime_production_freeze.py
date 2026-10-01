import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_084_final_one_runtime_production_freeze as q


class T(unittest.TestCase):

    def test_stack_exact(self):
        self.assertEqual(
            set(
                q.SOURCE_FILES
            ),
            {
                "QARB_080",
                "QARB_081",
                "QARB_082",
                "QARB_083",
            }
        )


    def test_required_horizons(self):
        self.assertEqual(
            q.REQUIRED_HORIZONS,
            {
                "2","5","15",
                "30","60","90"
            }
        )


    def test_runtime_horizon_is_90(self):
        self.assertEqual(
            q.q80.MAX_HORIZON_SECONDS,
            90.0
        )


    def test_proven_gate_preserved(self):
        self.assertEqual(
            q.q81.MIN_TOKEN_SAMPLES,
            30
        )

        self.assertEqual(
            q.q81.MIN_TOKEN_WIN_RATE,
            0.80
        )


    def test_one_launcher_state_contract(self):
        self.assertTrue(
            hasattr(
                q.q82,
                "STATE"
            )
        )

        self.assertTrue(
            callable(
                q.q82.run
            )
        )


    def test_restart_contract(self):
        self.assertTrue(
            callable(
                q.q83.compare
            )
        )

        self.assertTrue(
            callable(
                q.q83.snapshot
            )
        )


    def test_source_hashes(self):
        for path in q.SOURCE_FILES.values():
            self.assertTrue(
                path.is_file()
            )

            self.assertEqual(
                len(
                    q._sha(
                        path
                    )
                ),
                64
            )


    def test_authority_false(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q80.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q81.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q82.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q83.EXECUTION_AUTHORITY
        )


    def test_paper_only(self):
        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertTrue(
            q.q80.PAPER_ONLY
        )

        self.assertTrue(
            q.q81.PAPER_ONLY
        )

        self.assertTrue(
            q.q82.PAPER_ONLY
        )

        self.assertTrue(
            q.q83.PAPER_ONLY
        )


    def test_no_real_money(self):
        self.assertFalse(
            q.REAL_MONEY_MOVED
        )

        self.assertFalse(
            q.q80.REAL_MONEY_MOVED
        )

        self.assertFalse(
            q.q81.REAL_MONEY_MOVED
        )

        self.assertFalse(
            q.q82.REAL_MONEY_MOVED
        )

        self.assertFalse(
            q.q83.REAL_MONEY_MOVED
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
