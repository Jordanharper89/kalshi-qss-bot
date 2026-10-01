import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_085_two_second_executable_envelope_diagnostic as q


class T(unittest.TestCase):

    def test_2s_high_confidence_admits(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2.0":{
                        "samples":10,
                        "wins":9,
                        "pnl_sol":1.0
                    }
                }
            }
        )

        self.assertTrue(
            r["admitted"]
        )


    def test_2s_low_win_rate_rejects(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2":{
                        "samples":10,
                        "wins":7,
                        "pnl_sol":1.0
                    }
                }
            }
        )

        self.assertFalse(
            r["admitted"]
        )


    def test_2s_negative_pnl_rejects(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2":{
                        "samples":10,
                        "wins":9,
                        "pnl_sol":-0.1
                    }
                }
            }
        )

        self.assertFalse(
            r["admitted"]
        )


    def test_2s_sample_gate(self):
        r=q.two_second_evidence(
            {
                "horizons":{
                    "2":{
                        "samples":2,
                        "wins":2,
                        "pnl_sol":0.1
                    }
                }
            }
        )

        self.assertFalse(
            r["admitted"]
        )


    def test_compile_failure_reason(self):
        x=q.attempt_reason(
            {
                "compiled":False,
                "error":
                    "ATOMIC_TX_TOO_LARGE:1300"
            }
        )

        self.assertTrue(
            x.startswith(
                "COMPILE_FAIL:"
            )
        )


    def test_sim_error_reason(self):
        x=q.attempt_reason(
            {
                "compiled":True,
                "sim_err":{
                    "InstructionError":[
                        1,
                        "Custom"
                    ]
                },
                "sim_pnl_lamports":None,
            }
        )

        self.assertTrue(
            x.startswith(
                "SIM_ERROR:"
            )
        )


    def test_nonpositive_pnl_reason(self):
        x=q.attempt_reason(
            {
                "compiled":True,
                "sim_err":None,
                "sim_pnl_lamports":-1,
                "sim_bps":-1,
            }
        )

        self.assertEqual(
            x,
            "SIM_PNL_NONPOSITIVE"
        )


    def test_profitable_reason(self):
        x=q.attempt_reason(
            {
                "compiled":True,
                "sim_err":None,
                "sim_pnl_lamports":100,
                "sim_bps":100,
                "profitable":True,
            }
        )

        self.assertEqual(
            x,
            "PROFITABLE_SIMULATION"
        )


    def test_route_is_exact_existing_path(self):
        self.assertTrue(
            callable(
                q.las.compose_bound
            )
        )

        self.assertTrue(
            callable(
                q.las.q59.attempt_candidate_simulations
            )
        )


    def test_2s_policy(self):
        self.assertEqual(
            q.TARGET_HORIZON,
            "2"
        )

        self.assertEqual(
            q.MIN_2S_SAMPLES,
            3
        )

        self.assertEqual(
            q.MIN_2S_WIN_RATE,
            0.80
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
