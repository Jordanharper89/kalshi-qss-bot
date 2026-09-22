import unittest
from qseries_v2.oracle_adapters.kalshi.oad_006_kalshi_foundation import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_006_kalshi_adapter_foundation())
    def test_full_scope(self): self.assertEqual(build_kalshi_adapter_foundation().category_scope,"ALL")
    def test_read_only(self): self.assertFalse(build_kalshi_adapter_foundation().execution_authority)
if __name__=="__main__":
    print("="*72);print(" OAD-006 CERTIFICATION TEST");print(" KALSHI ADAPTER FOUNDATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Kalshi read-only full-category adapter foundation certified");print("[DONE] OAD-006 CERTIFIED")
