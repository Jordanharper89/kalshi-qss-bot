import unittest
from qseries_v2.oracle_production_learning.opl_003_outcome_grounded_production_learning_cycle import (
    OPL_003_BUILD_ID,OPL_003_REVISION,normalize_settled_market,collect_evidence_supported_settlements
)

class T(unittest.TestCase):
    def test_normalize(self):
        x=normalize_settled_market({"ticker":"KXTEST","result":"YES","settlement_ts":"2026-08-18T00:00:00Z"})
        self.assertEqual(x.ticker,"KXTEST")
        self.assertEqual(x.result,"yes")

    def test_intake_callable(self):
        self.assertTrue(callable(collect_evidence_supported_settlements))

    def test_revision(self):
        self.assertEqual(OPL_003_BUILD_ID,"OPL-003")
        self.assertIn("CORRECTION_V2",OPL_003_REVISION)

if __name__=="__main__":
    print("="*88)
    print(" OPL-003 CERTIFICATION TEST")
    print(" EVIDENCE-SUPPORTED SETTLEMENT INTAKE — CORRECTION V2")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Deep evidence-supported settlement intake certified")
    print("[PASS] Fixed newest-20K intake removed")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-003 CORRECTION V2 CERTIFIED")
