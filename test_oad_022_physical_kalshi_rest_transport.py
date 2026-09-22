import unittest
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_022_physical_kalshi_rest_transport())
    def test_get_only_manifest(self): self.assertEqual(build_oad_022_certification_manifest()["methods"],("GET",))
if __name__=="__main__":
    print("="*72);print(" OAD-022 CERTIFICATION TEST");print(" PHYSICAL KALSHI REST TRANSPORT");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Signed read-only Kalshi REST transport certified");print("[DONE] OAD-022 CERTIFIED")
