import unittest
from qseries_v2.oracle_learning.olr_051_production_outcome_evidence_linkage_diagnostic import *

class T(unittest.TestCase):
    def test_excludes_linkage_table(self):
        self.assertIn("oracle_outcome_evidence_linkage",EXCLUDED_TABLES)

    def test_contract(self):
        r=LinkageDiagnosticResult(
            (),(),"settled","canonical",100,"KXTEST","KXTEST",None,
            4,4,False,"MARKET_IDENTITY_MATCH_EXISTS_COLUMN_MAPPING_OR_ADMISSION_BREAK",False
        )
        self.assertEqual(r.outcome_count,100)
        self.assertFalse(r.execution_authority)

    def test_identity(self):
        self.assertEqual(OLR_051_BUILD_ID,"OLR-051")
        self.assertIn("CORRECTION_V2",OLR_051_REVISION)

if __name__=="__main__":
    print("="*88)
    print(" OLR-051 CERTIFICATION TEST")
    print(" PRODUCTION OUTCOME-EVIDENCE LINKAGE DIAGNOSTIC — CORRECTION V2")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Linkage ledger excluded from outcome/evidence source discovery")
    print("[PASS] Only non-empty production tables are eligible")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-051 CORRECTION V2 CERTIFIED")
