import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_095_micro_capital_exact_size_shadow_probe as q


class T(unittest.TestCase):

    def sample(self):
        return {
            "token":"T",
            "pump_pool":"P",
            "meteora_meta":{
                "address":"M",
                "token_x":"T",
                "token_y":"SOL",
                "decimals_x":6,
                "decimals_y":9,
            },
            "size_sol":1.4,
            "candidate":"C",
            "transaction_bytes":1158,
            "stability":{
                "cycles":3,
                "pass_rate":1.0,
            },
        }


    def test_exact_micro_sol(self):
        self.assertEqual(
            q.MICRO_TEST_SOL,
            0.001
        )


    def test_exact_micro_lamports(self):
        self.assertEqual(
            q.MICRO_TEST_LAMPORTS,
            1_000_000
        )


    def test_production_size_preserved(self):
        x=q.micro_copy(
            self.sample()
        )

        self.assertEqual(
            x[
                "production_size_sol"
            ],
            1.4
        )

        self.assertEqual(
            x[
                "size_sol"
            ],
            0.001
        )


    def test_hydration_uses_micro_size(self):
        x=q.micro_copy(
            self.sample()
        )

        y=q.hydration_bindings(
            [x]
        )

        self.assertEqual(
            y[0]["size_sol"],
            0.001
        )


    def test_micro_copy_marks_isolated(self):
        x=q.micro_copy(
            self.sample()
        )

        self.assertTrue(
            x[
                "micro_test_only"
            ]
        )


    def test_exact_094_source(self):
        self.assertTrue(
            str(
                q.q94.CERTIFIED
            ).endswith(
                "qarb_094_certified_execution_shadow_set.json"
            )
        )


    def test_exact_092_revalidation(self):
        self.assertTrue(
            callable(
                q.q92.revalidate_route
            )
        )


    def test_exact_087_simulator(self):
        self.assertTrue(
            callable(
                q.q87.simulate_candidate
            )
        )


    def test_no_production_write(self):
        with open(
            q.__file__,
            encoding="utf-8"
        ) as f:
            src=f.read()

        self.assertNotIn(
            "q94._save(",
            src
        )

        self.assertNotIn(
            "q93._save(",
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
