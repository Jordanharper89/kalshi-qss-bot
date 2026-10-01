import inspect
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_082_consolidated_one_runtime_cutover as q


class T(unittest.TestCase):

    def test_runtime_core_is_080(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "q80.run(",
            s
        )


    def test_classifier_is_081(self):
        s=inspect.getsource(
            q.certification_summary
        )

        self.assertIn(
            "q81.certify",
            s
        )


    def test_no_second_manual_runtime(self):
        s=inspect.getsource(
            q.run
        )

        self.assertNotIn(
            "subprocess.Popen",
            s
        )

        self.assertNotIn(
            "run_qarb_081",
            s
        )


    def test_dynamic_080_contract(self):
        self.assertTrue(
            callable(
                q.q80.select_rows
            )
        )

        self.assertTrue(
            callable(
                q.q80.run
            )
        )


    def test_proven_classifier_contract(self):
        self.assertTrue(
            callable(
                q.q81.certify
            )
        )

        self.assertEqual(
            q.q81.MIN_TOKEN_SAMPLES,
            30
        )

        self.assertEqual(
            q.q81.MIN_TOKEN_WIN_RATE,
            0.80
        )


    def test_080_transport_contract(self):
        self.assertGreaterEqual(
            q.q80.WS_CONNECTION_STAGGER_SECONDS,
            2.0
        )


    def test_080_horizon_contract(self):
        self.assertEqual(
            q.q80.MAX_HORIZON_SECONDS,
            90.0
        )


    def test_authority_false_everywhere(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q80.EXECUTION_AUTHORITY
        )

        self.assertFalse(
            q.q81.EXECUTION_AUTHORITY
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


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
