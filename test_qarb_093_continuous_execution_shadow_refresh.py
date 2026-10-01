import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_093_continuous_execution_shadow_refresh as q


class T(unittest.TestCase):

    def test_min_refresh(self):
        self.assertGreaterEqual(
            q.MIN_REFRESH_SECONDS,
            20.0
        )


    def test_exact_092_revalidation(self):
        self.assertTrue(
            callable(
                q.q92.revalidate_route
            )
        )


    def test_exact_092_fallback_sim(self):
        self.assertTrue(
            callable(
                q.q92.compile_and_simulate
            )
        )


    def test_exact_091_intake(self):
        self.assertTrue(
            callable(
                q.q91.intake_rows
            )
        )


    def test_exact_hydration(self):
        self.assertTrue(
            callable(
                q.q87.q86.hydrate
            )
        )


    def test_clean_sim(self):
        self.assertTrue(
            q.clean_sim({
                "compiled":True,
                "sim_err":None,
                "bytes":1158,
            })
        )


    def test_oversize_not_clean(self):
        self.assertFalse(
            q.clean_sim({
                "compiled":True,
                "sim_err":None,
                "bytes":1233,
            })
        )


    def test_failed_sim_not_clean(self):
        self.assertFalse(
            q.clean_sim({
                "compiled":True,
                "sim_err":{"x":1},
                "bytes":1158,
            })
        )


    def test_current_binding_state(self):
        self.assertTrue(
            str(
                q.CURRENT
            ).endswith(
                "qarb_093_current_execution_shadow_bindings.json"
            )
        )


    def test_history_is_jsonl(self):
        self.assertEqual(
            q.HISTORY.suffix,
            ".jsonl"
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
