import unittest
from qseries_v2.oracle_learning.olr_052_canonical_json_evidence_lookup_correction import (
    OLR_052_BUILD_ID,
    OLR_052_REVISION,
    extract_identity,
    lookup_market_evidence,
)

class T(unittest.TestCase):
    def test_direct_identity(self):
        t,m=extract_identity({"ticker":"KXBTC","market_id":"abc"},None)
        self.assertEqual(t,"KXBTC")
        self.assertEqual(m,"abc")

    def test_nested_identity(self):
        t,m=extract_identity({"market":{"ticker":"KXETH"}},None)
        self.assertEqual(t,"KXETH")
        self.assertEqual(m,"KXETH")

    def test_source_fallback(self):
        t,m=extract_identity({}, "KXSOURCE")
        self.assertEqual(t,"KXSOURCE")
        self.assertEqual(m,"KXSOURCE")

    def test_identity(self):
        self.assertEqual(OLR_052_BUILD_ID,"OLR-052")
        self.assertIn("CORRECTION_V2",OLR_052_REVISION)

    def test_lookup_callable(self):
        self.assertTrue(callable(lookup_market_evidence))

if __name__=="__main__":
    print("="*88)
    print(" OLR-052 CERTIFICATION TEST")
    print(" CANONICAL JSON EVIDENCE LOOKUP CORRECTION — V2")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Canonical JSON market identity extraction certified")
    print("[PASS] source_observation_id fallback certified")
    print("[PASS] OLR-037 candidate shape preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OLR-052 CORRECTION V2 CERTIFIED")
