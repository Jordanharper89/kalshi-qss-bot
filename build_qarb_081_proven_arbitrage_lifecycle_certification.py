from pathlib import Path
import py_compile

R = Path.cwd()

S = (
    R /
    "qseries_v2/oracle_strategy_intelligence/solana_money/"
    "qarb_execution_engineering"
)

M = S / "qarb_081_proven_arbitrage_lifecycle_certification.py"
T = R / "test_qarb_081_proven_arbitrage_lifecycle_certification.py"

if not M.is_file():
    raise SystemExit("[FAIL] current QARB-081 missing: " + str(M))

src = M.read_text(encoding="utf-8")

required = [
    'if lifecycle!="ACTIVE":',
    '"LIFECYCLE_NOT_ACTIVE"',
    '"PROVEN_PAPER_ARBITRAGE"',
    "MIN_TOKEN_SAMPLES=30",
    "MIN_TOKEN_WIN_RATE=0.80",
    "MIN_HORIZON_SAMPLES=3",
    "MIN_HORIZON_WIN_RATE=0.80",
]

missing = [x for x in required if x not in src]

if missing:
    raise SystemExit(
        "[FAIL] exact current QARB-081 contract changed: "
        + repr(missing)
    )


# ------------------------------------------------------------------
# RECHECK is an age/freshness state from QARB-072.
#
# It must NOT erase a historically proven arbitrage profile.
#
# RETIRED still fails.
# OBSERVE still fails.
#
# RECHECK carries requires_live_recheck=True so future execution
# must still prove a fresh executable opportunity before broadcast.
# ------------------------------------------------------------------

src = src.replace(
    '''    if lifecycle!="ACTIVE":
        reasons.append(
            "LIFECYCLE_NOT_ACTIVE"
        )''',

    '''    if lifecycle not in ("ACTIVE","RECHECK"):
        reasons.append(
            "LIFECYCLE_NOT_RECYCLABLE"
        )''',
    1
)


old_return = '''    return {
        "token":token,
        "classification":classification,
        "lifecycle":lifecycle,
        "samples":samples,
        "wins":wins,
        "win_rate":wr,
        "pnl_sol":pnl,
        "proven_horizons":
            proven_horizons,
        "horizons":
            horizons,
        "hold_reasons":
            reasons,
    }'''

new_return = '''    return {
        "token":token,
        "classification":classification,
        "lifecycle":lifecycle,
        "requires_live_recheck":(
            lifecycle=="RECHECK"
        ),
        "samples":samples,
        "wins":wins,
        "win_rate":wr,
        "pnl_sol":pnl,
        "proven_horizons":
            proven_horizons,
        "horizons":
            horizons,
        "hold_reasons":
            reasons,
    }'''

if old_return not in src:
    raise SystemExit(
        "[FAIL] exact classify return seam changed"
    )

src = src.replace(
    old_return,
    new_return,
    1
)


old_print = '''                x["pnl_sol"],
                ",".join(
                    x["proven_horizons"]
                )
            )
        )'''

new_print = '''                x["pnl_sol"],
                ",".join(
                    x["proven_horizons"]
                )
            )
        )

        if x["requires_live_recheck"]:
            print(
                "[LIVE_RECHECK_REQUIRED] token=%s "
                "historical_proven=True"%(
                    token[:10]
                )
            )'''

if old_print not in src:
    raise SystemExit(
        "[FAIL] exact proven print seam changed"
    )

src = src.replace(
    old_print,
    new_print,
    1
)

M.write_text(
    src,
    encoding="utf-8"
)


tests = r'''
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
'''

T.write_text(
    tests,
    encoding="utf-8"
)

py_compile.compile(
    str(M),
    doraise=True
)

py_compile.compile(
    str(T),
    doraise=True
)

print("[PASS] QARB-081 lifecycle semantics repaired in place")
print("[RECHECK] historical proven status preserved; fresh live validation still required")
print("[RETIRED] remains excluded from proven arbitrage")
print("[GATES] >=30 samples, >=80% overall WR, positive PnL unchanged")
print("[HORIZON] >=3 samples, >=80% horizon WR, positive PnL unchanged")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE real_money_moved=FALSE")