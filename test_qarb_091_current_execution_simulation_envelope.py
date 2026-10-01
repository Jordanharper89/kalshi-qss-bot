import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_091_current_execution_simulation_envelope as q


class T(unittest.TestCase):

    def row(self):
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
            "size_sol":0.28,
            "physical_net_lamports":100,
            "physical_net_bps":25.0,
        }


    def test_valid_intake(self):
        ok,reason=q.validate_intake_row(
            self.row()
        )

        self.assertTrue(ok)
        self.assertEqual(
            reason,
            "OK"
        )


    def test_negative_intake_rejected(self):
        x=self.row()
        x["physical_net_bps"]=-1

        ok,_=q.validate_intake_row(x)

        self.assertFalse(ok)


    def test_hydration_uses_selected_size(self):
        x=self.row()

        y=q.hydration_bindings(
            [x]
        )

        self.assertEqual(
            y[0]["size_sol"],
            0.28
        )


    def test_candidate_score_prefers_clean_sim(self):
        good={
            "compiled":True,
            "sim_err":None,
            "bytes":1200,
        }

        bad={
            "compiled":True,
            "sim_err":{
                "x":1
            },
            "bytes":1100,
        }

        self.assertLess(
            q.candidate_score(good),
            q.candidate_score(bad)
        )


    def test_candidate_score_prefers_legal_compile(self):
        a={
            "compiled":True,
            "bytes":1200,
        }

        b={
            "compiled":False
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


    def test_exact_087_repaired_candidates(self):
        self.assertTrue(
            callable(
                q.q87.repaired_candidates
            )
        )


    def test_exact_087_simulator(self):
        self.assertTrue(
            callable(
                q.q87.simulate_candidate
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

        self.assertIn(
            "None,",
            src
        )

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
