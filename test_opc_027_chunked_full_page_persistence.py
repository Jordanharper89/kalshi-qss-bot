import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_027_chunked_full_page_persistence import verify_opc_027_chunked_full_page_persistence

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_027_chunked_full_page_persistence())

if __name__=="__main__":
    print("="*80)
    print(" OPC-027 CERTIFICATION TEST")
    print(" CHUNKED FULL PAGE PERSISTENCE")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-027 certified")
    print("[DONE] OPC-027 CERTIFIED")
