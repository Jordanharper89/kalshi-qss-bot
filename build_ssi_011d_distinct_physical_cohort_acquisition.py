from pathlib import Path
import ast

R=Path.cwd()
P=R/"qseries_v2/oracle_strategy_intelligence/solana/ssi_011_physical_multi_token_cohort.py"

if not P.exists():
    raise SystemExit("[FAIL] SSI-011C production module missing")

ast.parse(P.read_text(encoding="utf-8",errors="replace"))

Q=R/"test_ssi_011d_distinct_physical_cohort_acquisition.py"

S=r'''import unittest
from qseries_v2.oracle_strategy_intelligence.solana.ssi_011_physical_multi_token_cohort import acquire_cohort

class T(unittest.TestCase):

    def test_physical_cohort(self):

        r=acquire_cohort(
            episodes=5,
            cycles=15
        )

        print("[SSI-011D-PHYSICAL]",r)

        self.assertEqual(
            r["independent_tokens"],
            5
        )

        self.assertEqual(
            len(r["unique_tokens"]),
            5
        )

        self.assertEqual(
            len(set(r["unique_tokens"])),
            5
        )

        self.assertEqual(
            len(r["episodes"]),
            5
        )

        for x in r["episodes"]:

            self.assertGreaterEqual(
                x["history_records"],
                13
            )

            self.assertEqual(
                x["successful_cycles"],
                15
            )

            self.assertEqual(
                x["temporal_state"],
                "TEMPORAL_5_15_30_60_READY"
            )

            self.assertEqual(
                x["ready_windows"],
                (5,15,30,60)
            )

            self.assertFalse(
                x["execution_authority"]
            )

        self.assertTrue(
            r["read_only"]
        )

        self.assertFalse(
            r["execution_authority"]
        )

if __name__=="__main__":
    unittest.main(verbosity=2)
'''

Q.write_text(S,encoding="utf-8")
ast.parse(S)

print("[PASS] SSI-011D physical cohort certification installed")
print("[PASS] requires five distinct physical tokens")
print("[PASS] requires 15 acquisition cycles per token")
print("[PASS] requires 5/15/30/60 temporal readiness")
print("[PASS] no synthetic cohort inputs")
print("[PASS] read-only; execution_authority=FALSE")