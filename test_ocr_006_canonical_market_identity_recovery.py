import unittest
from qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import *
class T(unittest.TestCase):
    def test_verifier(self):self.assertTrue(verify_ocr_006_canonical_market_identity_recovery())
    def test_nested_json(self):
        x=recover_market_identity({"observation_id":"o","payload":"{\"msg\":{\"ticker\":\"KXTEST-1\"}}"})
        self.assertEqual(x.market_ticker,"KXTEST-1")
    def test_unresolved(self):self.assertFalse(recover_market_identity({"observation_id":"o","payload":{"x":1}}).recovered)
if __name__=="__main__":
    print("="*72);print(" OCR-006 CERTIFICATION TEST");print(" CANONICAL MARKET IDENTITY RECOVERY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():raise SystemExit(1)
    print("[PASS] Nested persisted Kalshi market identity recovery certified");print("[DONE] OCR-006 CERTIFIED")
