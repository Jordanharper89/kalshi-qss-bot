import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_092_just_in_time_execution_revalidation_gate as q


class T(unittest.TestCase):

    def test_candidate_score_clean_first(self):
        good={
            "compiled":True,
            "sim_err":None,
            "bytes":1200,
        }

        bad={
            "compiled":True,
            "sim_err":{"x":1},
            "bytes":1100,
        }

        self.assertLess(
            q.candidate_score(good),
            q.candidate_score(bad)
        )


    def test_candidate_score_smaller_clean(self):
        a={
            "compiled":True,
            "sim_err":None,
            "bytes":1190,
        }

        b={
            "compiled":True,
            "sim_err":None,
            "bytes":1229,
        }

        self.assertLess(
            q.candidate_score(a),
            q.candidate_score(b)
        )


    def test_max_tx_bytes(self):
        self.assertEqual(
            q.MAX_TX_BYTES,
            1232
        )


    def test_exact_087_compose(self):
        self.assertTrue(
            callable(
                q.q87.compose
            )
        )


    def test_exact_087_simulator(self):
        self.assertTrue(
            callable(
                q.q87.simulate_candidate
            )
        )


    def test_exact_091_intake(self):
        self.assertTrue(
            callable(
                q.q91.intake_rows
            )
        )


    def test_exact_091_validation(self):
        self.assertTrue(
            callable(
                q.q91.validate_intake_row
            )
        )


    def test_exact_086_hydration(self):
        self.assertTrue(
            callable(
                q.q87.q86.hydrate
            )
        )


    def test_no_private_key_requirement(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "require_local_identity",
            src
        )

        self.assertIn(
            "None,",
            src
        )


    def test_no_broadcast(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "sendTransaction",
            src
        )

        self.assertNotIn(
            "c.send(",
            src
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
    unittest.main(
        verbosity=2
    )
