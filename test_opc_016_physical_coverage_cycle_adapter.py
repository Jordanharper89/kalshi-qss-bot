import unittest
from qseries_v2.oracle_pre_settlement_coverage.opc_016_physical_coverage_cycle_adapter import verify_opc_016_physical_coverage_cycle_adapter

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(verify_opc_016_physical_coverage_cycle_adapter())

if __name__=="__main__":
    print("="*72)
    print(" OPC-016 CERTIFICATION TEST")
    print(" PHYSICAL COVERAGE CYCLE ADAPTER")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OPC-016 certified")
    print("[DONE] OPC-016 CERTIFIED")
