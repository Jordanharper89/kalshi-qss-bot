
import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_081_proven_arbitrage_lifecycle_certification as q


class T(unittest.TestCase):

    def token(
        self,
        samples=40,
        wins=36,
        pnl=1.0
    ):
        return {
            "samples":samples,
            "wins":wins,
            "pnl_sol":pnl,
            "status":"ACTIVE",
            "horizons":{
                "2":{
                    "samples":10,
                    "wins":9,
                    "pnl_sol":0.2
                },
                "5":{
                    "samples":10,
                    "wins":9,
                    "pnl_sol":0.2
                },
            }
        }


    def test_active_high_confidence_proven(self):
        x=q.classify_token(
            "A",
            self.token(),
            "ACTIVE"
        )

        self.assertEqual(
            x["classification"],
            "PROVEN_PAPER_ARBITRAGE"
        )

        self.assertFalse(
            x["requires_live_recheck"]
        )


    def test_recheck_preserves_historical_proven(self):
        x=q.classify_token(
            "A",
            self.token(),
            "RECHECK"
        )

        self.assertEqual(
            x["classification"],
            "PROVEN_PAPER_ARBITRAGE"
        )

        self.assertTrue(
            x["requires_live_recheck"]
        )


    def test_retired_never_proven(self):
        x=q.classify_token(
            "A",
            self.token(),
            "RETIRED"
        )

        self.assertEqual(
            x["classification"],
            "RESEARCH"
        )

        self.assertIn(
            "LIFECYCLE_NOT_RECYCLABLE",
            x["hold_reasons"]
        )


    def test_observe_never_proven(self):
        x=q.classify_token(
            "A",
            self.token(),
            "OBSERVE"
        )

        self.assertEqual(
            x["classification"],
            "RESEARCH"
        )


    def test_55_percent_stays_research(self):
        x=q.classify_token(
            "A",
            self.token(
                samples=40,
                wins=22,
                pnl=1.0
            ),
            "RECHECK"
        )

        self.assertEqual(
            x["classification"],
            "RESEARCH"
        )

        self.assertIn(
            "TOKEN_WIN_RATE_BELOW_PROVEN_GATE",
            x["hold_reasons"]
        )


    def test_negative_pnl_stays_research(self):
        x=q.classify_token(
            "A",
            self.token(
                pnl=-0.1
            ),
            "RECHECK"
        )

        self.assertEqual(
            x["classification"],
            "RESEARCH"
        )


    def test_insufficient_samples_stays_research(self):
        x=q.classify_token(
            "A",
            self.token(
                samples=22,
                wins=22,
                pnl=1.0
            ),
            "RECHECK"
        )

        self.assertEqual(
            x["classification"],
            "RESEARCH"
        )

        self.assertIn(
            "INSUFFICIENT_TOKEN_SAMPLES",
            x["hold_reasons"]
        )


    def test_horizon_gate(self):
        x=self.token()

        x["horizons"]["15"]={
            "samples":10,
            "wins":5,
            "pnl_sol":0.2
        }

        r=q.classify_token(
            "A",
            x,
            "RECHECK"
        )

        self.assertNotIn(
            "15",
            r["proven_horizons"]
        )

        self.assertIn(
            "2",
            r["proven_horizons"]
        )


    def test_restart_monotonic_pass(self):
        previous={
            "continuity_anchor":{
                "tokens":{
                    "A":{
                        "samples":30,
                        "wins":25
                    }
                },
                "seen_tokens":["A"],
                "memory_tokens":["A"],
            }
        }

        current={
            "A":{
                "samples":31,
                "wins":26
            }
        }

        r=q.continuity_check(
            previous,
            current,
            {"A"},
            {"A"}
        )

        self.assertEqual(
            r["status"],
            "PASS"
        )


    def test_restart_rollback_holds(self):
        previous={
            "continuity_anchor":{
                "tokens":{
                    "A":{
                        "samples":30,
                        "wins":25
                    }
                },
                "seen_tokens":["A"],
                "memory_tokens":["A"],
            }
        }

        current={
            "A":{
                "samples":29,
                "wins":24
            }
        }

        r=q.continuity_check(
            previous,
            current,
            set(),
            set()
        )

        self.assertEqual(
            r["status"],
            "HOLD"
        )


    def test_gate_constants_unchanged(self):
        self.assertEqual(
            q.MIN_TOKEN_SAMPLES,
            30
        )

        self.assertEqual(
            q.MIN_TOKEN_WIN_RATE,
            0.80
        )

        self.assertEqual(
            q.MIN_HORIZON_SAMPLES,
            3
        )

        self.assertEqual(
            q.MIN_HORIZON_WIN_RATE,
            0.80
        )


    def test_required_horizons_contract(self):
        self.assertEqual(
            q.REQUIRED_HORIZONS,
            {
                "2","5","15",
                "30","60","90"
            }
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
