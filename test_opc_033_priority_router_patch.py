import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_033_priority_router_patch import verify_opc_033_priority_router_patch

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_033_priority_router_patch())

if __name__=="__main__":
    print("="*80)
    print(" OPC-033 CERTIFICATION TEST")
    print(" PRIORITY ROUTER PATCH")
    print("="*80)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-033 certified")
    print("[DONE] OPC-033 CERTIFIED")
