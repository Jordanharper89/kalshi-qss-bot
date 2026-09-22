import unittest
from qseries_v2.oracle_adapters.kalshi.oad_023_real_universe_acquisition import *
class T(unittest.TestCase):
    def test_verifier(self): self.assertTrue(verify_oad_023_real_kalshi_full_universe_acquisition())
    def test_limit(self): self.assertEqual(build_oad_023_certification_manifest()["page_limit"],1000)
if __name__=="__main__":
    print("="*72);print(" OAD-023 CERTIFICATION TEST");print(" REAL KALSHI FULL-UNIVERSE ACQUISITION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] Physical full-universe acquisition implementation certified");print("[DONE] OAD-023 CERTIFIED")
