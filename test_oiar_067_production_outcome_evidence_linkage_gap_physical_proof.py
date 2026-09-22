import unittest
from pathlib import Path
import qseries_v2.oracle_intelligence_analytics_runtime.oiar_067_production_outcome_evidence_linkage_gap_physical_proof as m

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(m.verify_oiar_067_production_outcome_evidence_linkage_gap_physical_proof())

    def test_physical_gap(self):
        x=m.physical_probe(Path.cwd(),25)
        self.assertGreater(x["sampled_missing_settlements"],0)
        self.assertEqual(
            x["exact_ticker_pre_settlement_found"]+
            x["exact_ticker_only_post_settlement"]+
            x["exact_ticker_no_evidence"],
            x["sampled_missing_settlements"],
        )
        self.assertTrue(x["read_only"])
        self.assertEqual(x["repaired_rows"],0)
        self.assertFalse(x["probability_enabled"])
        self.assertFalse(x["execution_authority"])

if __name__=="__main__":
    print("="*88)
    print(" OIAR-067 CERTIFICATION TEST")
    print(" PRODUCTION OUTCOME/EVIDENCE LINKAGE GAP PHYSICAL PROOF")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] EVIDENCE_MISSING sample physically classified")
    print("[PASS] exact ticker evidence checked")
    print("[PASS] strict pre-settlement evidence checked")
    print("[PASS] read-only proof preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-067 CERTIFIED")
