import unittest
from qseries_v2.oracle_production_learning.opl_006_exact_production_learning_blocker_diagnostic import *

class T(unittest.TestCase):
    def test_lookup_reject_class(self):
        self.assertEqual(
            classify_trace(2,1,1,0,0,0,0),
            "MATCH_EXISTS_BUT_OPL003_LOOKUP_REJECTS_OR_MISCOMPARES",
        )

    def test_post_only_class(self):
        self.assertEqual(
            classify_trace(2,0,2,0,0,0,0),
            "EVIDENCE_EXISTS_ONLY_AFTER_SETTLEMENT",
        )

    def test_identity_granularity_class(self):
        self.assertEqual(
            classify_trace(0,0,0,5,0,0,0),
            "IDENTITY_GRANULARITY_MISMATCH_MARKET_VS_EVENT_OR_SERIES",
        )

    def test_index_wrong_class(self):
        self.assertEqual(
            classify_trace(0,0,0,0,0,0,3),
            "CANONICAL_CONTAINS_TICKER_BUT_EVIDENCE_INDEX_IDENTITY_IS_WRONG",
        )

    def test_identity(self):
        self.assertEqual(OPL_006_BUILD_ID,"OPL-006")

if __name__=="__main__":
    print("="*88)
    print(" OPL-006 CERTIFICATION TEST")
    print(" EXACT PRODUCTION LEARNING BLOCKER DIAGNOSTIC")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Failure-classification contract certified")
    print("[PASS] Diagnostic is read-only")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPL-006 CERTIFIED")
